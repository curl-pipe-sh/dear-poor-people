{
  description = "poor-tools web installer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      flake-parts,
      nixpkgs,
      pre-commit-hooks,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      flake = {
        # System-agnostic NixOS module, available as `nixosModules.default`
        nixosModules.default =
          {
            config,
            lib,
            pkgs,
            ...
          }:
          let
            cfg = config.services.poor-installer-web;
            pkg = self.packages.${config.nixpkgs.hostPlatform.system}.poor-installer-web;
          in
          {
            options.services.poor-installer-web = {
              enable = lib.mkEnableOption "poor-tools web installer";

              bindPort = lib.mkOption {
                type = lib.types.port;
                default = 7667;
                description = "Port to listen on";
              };

              bindHost = lib.mkOption {
                type = lib.types.str;
                default = "127.0.0.1";
                description = "Host to bind to";
              };
            };

            config = lib.mkIf cfg.enable {
              systemd.services.poor-installer-web = {
                description = "poor-tools web installer";
                wantedBy = [ "multi-user.target" ];
                after = [ "network.target" ];

                environment = {
                  BIND_HOST = cfg.bindHost;
                  BIND_PORT = toString cfg.bindPort;
                };

                serviceConfig = {
                  Type = "simple";
                  ExecStart = "${pkg}/bin/poor-installer-web";
                  Restart = "always";
                  RestartSec = 10;

                  # Security hardening
                  DynamicUser = true;
                  NoNewPrivileges = true;
                  ProtectSystem = "strict";
                  ProtectHome = true;
                  PrivateTmp = true;
                  PrivateDevices = true;
                  ProtectHostname = true;
                  ProtectClock = true;
                  ProtectKernelTunables = true;
                  ProtectKernelModules = true;
                  ProtectKernelLogs = true;
                  ProtectControlGroups = true;
                  RestrictNamespaces = true;
                  LockPersonality = true;
                  MemoryDenyWriteExecute = true;
                  RestrictRealtime = true;
                  RestrictSUIDSGID = true;
                  RemoveIPC = true;
                };
              };
            };
          };
      };

      perSystem =
        {
          self',
          pkgs,
          system,
          ...
        }:
        let
          pythonEnv = pkgs.python313.withPackages (
            ps: with ps; [
              fastapi
              uvicorn
            ]
          );

          cleanSrc = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter =
              path: type:
              let
                baseName = builtins.baseNameOf path;
              in
              # Include everything except build artifacts and .git
              !(pkgs.lib.hasInfix "result" path)
              && !(pkgs.lib.hasInfix ".git" path)
              && !(pkgs.lib.hasInfix "__pycache__" path)
              && !(pkgs.lib.hasInfix ".pytest_cache" path)
              && !(pkgs.lib.hasInfix ".venv" path)
              && !(pkgs.lib.hasInfix ".ruff_cache" path)
              && !(pkgs.lib.hasInfix ".mypy_cache" path);
          };

          poor-installer-web = pkgs.python313Packages.buildPythonPackage {
            pname = "poor-installer-web";
            version = "0.1.0";
            pyproject = true;
            src = cleanSrc;

            nativeBuildInputs = with pkgs.python313Packages; [
              hatchling
            ];

            propagatedBuildInputs = with pkgs.python313Packages; [
              fastapi
              uvicorn
            ];

            # Sanity check import at build time
            pythonImportsCheck = [ "poor_installer_web" ];

            meta = with pkgs.lib; {
              description = "Web installer for poor-tools command-line utilities";
              homepage = "https://github.com/pschmitt/poor-tools";
              license = licenses.gpl3Only;
              maintainers = [ maintainers.pschmitt ];
              platforms = platforms.all;
              mainProgram = "poor-installer-web";
            };
          };

          dockerImage = pkgs.dockerTools.buildLayeredImage {
            name = "poor-installer-web";
            tag = "latest";

            contents = [
              pythonEnv
              pkgs.bash
              pkgs.coreutils
              pkgs.curl
              pkgs.wget
            ];

            config = {
              Cmd = [ "${poor-installer-web}/bin/poor-installer-web" ];
              WorkingDir = "${poor-installer-web}/share/poor-installer-web";
              ExposedPorts."7667/tcp" = { };
              Env = [
                "BIND_HOST=0.0.0.0"
                "BIND_PORT=7667"
                "PYTHONUNBUFFERED=1"
              ];
              Healthcheck = {
                Test = [
                  "CMD-SHELL"
                  "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:7667/health').read()\" || exit 1"
                ];
                Interval = 30000000000; # 30s in nanoseconds
                Timeout = 3000000000; # 3s
                StartPeriod = 5000000000; # 5s
                Retries = 3;
              };
            };
          };

          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              # Python formatting and linting
              ruff = {
                enable = true;
              };
              ruff-format = {
                enable = true;
              };

              # Type checking
              mypy = {
                enable = true;
                files = "poor_installer_web/.*\\.py$";
              };

              # Tests
              pytest = {
                enable = true;
                name = "pytest";
                entry = "${pythonEnv}/bin/python -m pytest tests/ -v";
                language = "system";
                files = "\\.py$";
                pass_filenames = false;
              };

              # Docker linting
              hadolint = {
                enable = true;
              };

              # Shell linting
              shellcheck = {
                enable = true;
              };

              # Nix formatting
              nixfmt-rfc-style = {
                enable = true;
              };
            };
          };
        in
        {
          packages = {
            default = poor-installer-web;
            poor-installer-web = poor-installer-web;
            docker = dockerImage;
          };

          apps.default = {
            type = "app";
            program = "${self'.packages.poor-installer-web}/bin/poor-installer-web";
          };

          devShells.default = pkgs.mkShell {
            buildInputs =
              with pkgs;
              [
                pythonEnv
                python313Packages.pytest
                python313Packages.pytest-asyncio
                python313Packages.httpx
                python313Packages.mypy
                python313Packages.types-requests
                ruff
                uv
                hadolint
                shellcheck
                nixfmt-rfc-style
              ]
              ++ pre-commit-check.enabledPackages;

            shellHook = ''
              ${pre-commit-check.shellHook}
              echo "🔧 poor-tools web installer dev environment"
              echo "==========================================="
              echo "Python: $(python --version)"
              echo "FastAPI available with uvicorn"
              echo ""
              echo "Commands:"
              echo "  python -m poor_installer_web.app         # Start server"
              echo "  uvicorn poor_installer_web.app:app --reload --port 7667    # Development server"
              echo "  uv run pytest tests/ -v                  # Run tests"
              echo "  ruff check . && ruff format .            # Format code"
              echo "  mypy poor_installer_web/app.py           # Type check"
              echo "  nix build '.#docker'                     # Build Docker image"
              echo ""
              echo "Pre-commit hooks are installed and will run on commit."
              echo "To run manually: pre-commit run --all-files"
            '';
          };
        };
    };
}
