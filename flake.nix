{
  description = "poor-tools web installer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pre-commit-hooks = {
      url = "github:cachix/pre-commit-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      pre-commit-hooks,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python313;

        pythonEnv = python.withPackages (ps: with ps; [
          fastapi
          uvicorn
        ]);

        pre-commit-check = pre-commit-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            # Python formatting and linting
            ruff = {
              enable = true;
              # args = [ "check" "--fix" ];
            };
            ruff-format = {
              enable = true;
            };

            # Import sorting
            ruff-import-sort = {
              enable = true;
              name = "ruff import sort";
              entry = "${pkgs.ruff}/bin/ruff check --select I --fix";
              language = "system";
              files = "\\.py$";
            };

            # Type checking
            mypy = {
              enable = true;
              files = "main\\.py$";
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

            # Trailing whitespace
            trailing-whitespace = {
              enable = true;
              name = "trailing-whitespace";
              entry = "${pkgs.python3}/bin/python -m pre_commit_hooks.trailing_whitespace_fixer";
              language = "system";
            };

            # End of file newline
            end-of-file-fixer = {
              enable = true;
              name = "end-of-file-fixer";
              entry = "${pkgs.python3}/bin/python -m pre_commit_hooks.end_of_file_fixer";
              language = "system";
            };
          };
        };

        poor-tools-web = pkgs.stdenv.mkDerivation {
          pname = "poor-tools-web";
          version = "0.1.0";

          # Include all files and directories explicitly
          src = pkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type:
              let
                baseName = baseNameOf path;
              in
                # Include everything except build artifacts and .git
                !(pkgs.lib.hasInfix "result" path) &&
                !(pkgs.lib.hasInfix ".git" path) &&
                !(pkgs.lib.hasInfix "__pycache__" path) &&
                !(pkgs.lib.hasInfix ".pytest_cache" path) &&
                !(pkgs.lib.hasInfix ".venv" path) &&
                !(pkgs.lib.hasInfix ".ruff_cache" path) &&
                !(pkgs.lib.hasInfix ".mypy_cache" path);
          };

          nativeBuildInputs = [
            pythonEnv
          ];

          buildPhase = ''
            mkdir -p $out/share/poor-tools-web

            # Copy all source files
            cp -r * $out/share/poor-tools-web/

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

          installPhase = "true"; # Already done in buildPhase
        };
      in
      {
        packages = {
          default = poor-tools-web;
          poor-tools-web = poor-tools-web;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.ruff
            pkgs.uv
            pkgs.hadolint
            pre-commit-check.enabledPackages
          ] ++ (with python.pkgs; [
            pytest
            pytest-asyncio
            httpx
            mypy
          ]);

          shellHook = ''
            ${pre-commit-check.shellHook}
            echo "poor-tools web installer dev environment"
            echo "Run: uvicorn main:app --reload --host 127.0.0.1 --port 7667"
            echo "Or: python main.py"
            echo ""
            echo "Pre-commit hooks are installed and will run on commit."
            echo "To run manually: pre-commit run --all-files"
          '';
        };

        nixosModules.default =
          {
            config,
            lib,
            pkgs,
            ...
          }:
          with lib;
          let
            cfg = config.services.poor-tools-web;
          in
          {
            options.services.poor-tools-web = {
              enable = mkEnableOption "poor-tools web installer";

              bindPort = mkOption {
                type = types.int;
                default = 7667;
                description = "Port to listen on";
              };

              bindHost = mkOption {
                type = types.str;
                default = "127.0.0.1";
                description = "Host to bind to";
              };
            };

            config = mkIf cfg.enable {
              systemd.services.poor-tools-web = {
                description = "poor-tools web installer";
                wantedBy = [ "multi-user.target" ];
                after = [ "network.target" ];

                serviceConfig = {
                  Type = "exec";
                  ExecStart = "${poor-tools-web}/bin/poor-tools-web";
                  Environment = [
                    "BIND_HOST=${cfg.bindHost}"
                    "BIND_PORT=${toString cfg.bindPort}"
                  ];
                  Restart = "always";
                  RestartSec = 5;

                  # Security
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
      }
    );
}
