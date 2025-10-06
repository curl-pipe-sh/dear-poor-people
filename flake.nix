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

      imports = [
        inputs.pre-commit-hooks.flakeModule
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
            cfg = config.services.poor-tools-web;
            pkg = self.packages.${config.nixpkgs.hostPlatform.system}.poor-tools-web;
          in
          {
            options.services.poor-tools-web = {
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
              systemd.services.poor-tools-web = {
                description = "poor-tools web installer";
                wantedBy = [ "multi-user.target" ];
                after = [ "network.target" ];

                environment = {
                  BIND_HOST = cfg.bindHost;
                  BIND_PORT = toString cfg.bindPort;
                };

                serviceConfig = {
                  Type = "exec";
                  ExecStart = "${pkg}/bin/poor-tools-web";
                  Restart = "always";
                  RestartSec = 5;

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
          config,
          pkgs,
          system,
          ...
        }:
        let
          python = pkgs.python313;

          pythonEnv = python.withPackages (
            ps: with ps; [
              fastapi
              uvicorn
            ]
          );

          cleanSrc = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter =
              path: type:
              pkgs.lib.cleanSourceFilter path type
              && !(pkgs.lib.hasInfix "result" path)
              && !(pkgs.lib.hasInfix "__pycache__" path)
              && !(pkgs.lib.hasInfix ".pytest_cache" path)
              && !(pkgs.lib.hasInfix ".venv" path)
              && !(pkgs.lib.hasInfix ".ruff_cache" path)
              && !(pkgs.lib.hasInfix ".mypy_cache" path);
          };

          poor-tools-web = pkgs.stdenv.mkDerivation {
            pname = "poor-tools-web";
            version = "0.1.0";
            src = cleanSrc;

            nativeBuildInputs = [
              pythonEnv
            ];

            buildPhase = ''
              mkdir -p $out/share/poor-tools-web

              # Copy all source files
              cp -r * $out/share/poor-tools-web/

              # Copy hidden files if they exist
              cp -r .github $out/share/poor-tools-web/ 2>/dev/null || true
              cp .gitignore $out/share/poor-tools-web/ 2>/dev/null || true
              cp .hadolint.yaml $out/share/poor-tools-web/ 2>/dev/null || true

              # Create wrapper script
              mkdir -p $out/bin
              cat > $out/bin/poor-tools-web << EOF
              #!/usr/bin/env bash
              cd $out/share/poor-tools-web
              export BIND_HOST=\''${BIND_HOST:-0.0.0.0}
              export BIND_PORT=\''${BIND_PORT:-7667}
              exec ${pythonEnv}/bin/python main.py "\$@"
              EOF
              chmod +x $out/bin/poor-tools-web
            '';

            installPhase = "true";

            meta = with pkgs.lib; {
              description = "Web installer for poor-tools command-line utilities";
              homepage = "https://github.com/pschmitt/poor-tools";
              license = licenses.gpl3Only;
              maintainers = [ ];
              platforms = platforms.all;
              mainProgram = "poor-tools-web";
            };
          };

          dockerImage = pkgs.dockerTools.buildLayeredImage {
            name = "poor-tools-web";
            tag = "latest";

            contents = [
              pythonEnv
              pkgs.bash
              pkgs.coreutils
              pkgs.curl
              pkgs.wget
            ];

            config = {
              Cmd = [ "${poor-tools-web}/bin/poor-tools-web" ];
              WorkingDir = "${poor-tools-web}/share/poor-tools-web";
              ExposedPorts."7667/tcp" = { };
              Env = [
                "BIND_HOST=0.0.0.0"
                "BIND_PORT=7667"
                "PYTHONUNBUFFERED=1"
              ];
              Healthcheck = {
                Test = [
                  "CMD-SHELL"
                  "curl -f http://localhost:7667/health || exit 1"
                ];
                Interval = 30000000000; # 30s in nanoseconds
                Timeout = 3000000000; # 3s
                StartPeriod = 5000000000; # 5s
                Retries = 3;
              };
            };
          };
        in
        {
          pre-commit = {
            check.enable = true;
            settings = {
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
                  files = "main\\.py$";
                };

                # Nix formatting
                nixfmt-rfc-style = {
                  enable = true;
                };
              };
            };
          };

          packages = {
            default = poor-tools-web;
            poor-tools-web = poor-tools-web;
            docker = dockerImage;
          };

          apps.default = {
            type = "app";
            program = "${self'.packages.poor-tools-web}/bin/poor-tools-web";
          };

          devShells.default = pkgs.mkShell {
            buildInputs = [
              pythonEnv
              pkgs.ruff
              pkgs.uv
              pkgs.hadolint
              pkgs.nixfmt-rfc-style
              pkgs.statix
            ]
            ++ (with python.pkgs; [
              pytest
              pytest-asyncio
              httpx
              mypy
            ]);

            shellHook = ''
              ${config.pre-commit.installationScript}
              echo "🔧 poor-tools web installer dev environment"
              echo "==========================================="
              echo "Python: $(python --version)"
              echo "FastAPI available with uvicorn"
              echo ""
              echo "Commands:"
              echo "  python main.py                           # Start server"
              echo "  uvicorn main:app --reload --port 7667    # Development server"
              echo "  uv run pytest tests/ -v                  # Run tests"
              echo "  ruff check . && ruff format .             # Format code"
              echo "  mypy main.py                             # Type check"
              echo "  nix build '.#docker'                     # Build Docker image"
              echo ""
              echo "Pre-commit hooks are installed and will run on commit."
              echo "To run manually: pre-commit run --all-files"
            '';
          };
        };
    };
}
