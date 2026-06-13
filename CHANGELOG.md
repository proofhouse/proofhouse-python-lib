# Changelog

## [v0.1.0](https://github.com/proofhouse/proofhouse-python-lib/compare/3a9aa87a2576bde590454798937e6999fe0c1758..v0.1.0) - 2026-06-13

### Features

- add canonical formatter (#14) - ([2f9dcd9](https://github.com/proofhouse/proofhouse-python-lib/commit/2f9dcd96f6c1a24ba9de344c23c6bd5ac2619853)) - [@tbhb](https://github.com/tbhb)
- add exact-arithmetic evaluator (#13) - ([56dd86e](https://github.com/proofhouse/proofhouse-python-lib/commit/56dd86ee6125247fafe0fd421dfaac69757bf6f1)) - [@tbhb](https://github.com/tbhb)
- add expression AST and parser (#3) - ([e60dd31](https://github.com/proofhouse/proofhouse-python-lib/commit/e60dd3177b68693642e29c443bfcce70685883b1)) - [@tbhb](https://github.com/tbhb)
- add expression tokens and lexer - ([37f71a3](https://github.com/proofhouse/proofhouse-python-lib/commit/37f71a38e781cdd5a2ac2d7eef7645388d13aae9)) - [@tbhb](https://github.com/tbhb)
- add package version metadata and py.typed marker - ([a7f2305](https://github.com/proofhouse/proofhouse-python-lib/commit/a7f230574a3f6984cde8311aac9a0c4afb9f2042)) - [@tbhb](https://github.com/tbhb)
- add pyproject.toml with uv_build backend - ([9ed74d5](https://github.com/proofhouse/proofhouse-python-lib/commit/9ed74d54144ec46081243194aeda8790eb8580d3)) - [@tbhb](https://github.com/tbhb)

#### Documentation

- add agent instructions and worktree rules - ([16721f9](https://github.com/proofhouse/proofhouse-python-lib/commit/16721f944eea243b07090aaa1b1f7c20d102f46e)) - [@tbhb](https://github.com/tbhb)

#### Build system

- (**deps**) commit uv.lock and add lock-check drift gate - ([fff3b6f](https://github.com/proofhouse/proofhouse-python-lib/commit/fff3b6f3b83a3d0c6fff25bccae60bc8976291a9)) - [@tbhb](https://github.com/tbhb)
- make wheel builds reproducible - ([d060ac7](https://github.com/proofhouse/proofhouse-python-lib/commit/d060ac7ae311a26c11f9ea378fa4c80825eb78ae)) - [@tbhb](https://github.com/tbhb)
- add minimal Justfile with build and test recipes - ([9e8b431](https://github.com/proofhouse/proofhouse-python-lib/commit/9e8b4319842cec63566cf090bb1ef71449f1a75a)) - [@tbhb](https://github.com/tbhb)

#### Continuous Integration

- (**actions**) add CodeQL scanning for Python and Actions (#22) - ([e7723e6](https://github.com/proofhouse/proofhouse-python-lib/commit/e7723e6de62664461262922197eccfa507364e49)) - [@tbhb](https://github.com/tbhb)
- (**actions**) add security.yml with osv-scanner SARIF uploads (#21) - ([d5e05ee](https://github.com/proofhouse/proofhouse-python-lib/commit/d5e05ee2d7dbac4420e0ce9b505579bfdef879ef)) - [@tbhb](https://github.com/tbhb)
- (**actions**) consume shared lint-workflows and lint-codeowners workflows - ([1514f4b](https://github.com/proofhouse/proofhouse-python-lib/commit/1514f4b6901d96a9ec30d9ef1815e3aa84af5057)) - [@tbhb](https://github.com/tbhb)
- (**actions**) add ci.yml with matrixed test and lock-check jobs - ([4426e35](https://github.com/proofhouse/proofhouse-python-lib/commit/4426e3519ba5669c8d23d62365ecb06f83278a51)) - [@tbhb](https://github.com/tbhb)
- add bandit security gate (#20) - ([3573b4b](https://github.com/proofhouse/proofhouse-python-lib/commit/3573b4b20ff12c88b43838a39c283eac288d9877)) - [@tbhb](https://github.com/tbhb)
- add pip-audit dependency vulnerability gate (#19) - ([92280bd](https://github.com/proofhouse/proofhouse-python-lib/commit/92280bd2305fd1e4345800de887cf0126f0106d8)) - [@tbhb](https://github.com/tbhb)
- default vale output to the agent template - ([c65450f](https://github.com/proofhouse/proofhouse-python-lib/commit/c65450f27bdb9f8ed193a45df8fad2561d5819ad)) - [@tbhb](https://github.com/tbhb)
- adopt the shared proofhouse vale package - ([92cb46c](https://github.com/proofhouse/proofhouse-python-lib/commit/92cb46c76c65dfa117a5fad504fc59d180e57b9d)) - [@tbhb](https://github.com/tbhb)
- add gitleaks secret scanning (#18) - ([8042175](https://github.com/proofhouse/proofhouse-python-lib/commit/804217521d82628e7f5c1ea5dc1991e365a44c1f)) - [@tbhb](https://github.com/tbhb)
- add lint aggregators across the toolchain (#12) - ([a0d16eb](https://github.com/proofhouse/proofhouse-python-lib/commit/a0d16eb1f75a4c769cd5e759c2850208eabd25b8)) - [@tbhb](https://github.com/tbhb)
- add reuse SPDX compliance gate (#11) - ([46cf16f](https://github.com/proofhouse/proofhouse-python-lib/commit/46cf16f913653d5ee4e596eeebf211cc973dead2)) - [@tbhb](https://github.com/tbhb)
- add import-linter architecture contracts (#7) - ([83773bb](https://github.com/proofhouse/proofhouse-python-lib/commit/83773bb05043e9fd791d5b946ea677968ef94092)) - [@tbhb](https://github.com/tbhb)
- add pylint duplicate-code gate (#6) - ([381f4c2](https://github.com/proofhouse/proofhouse-python-lib/commit/381f4c2bedfda5c39011c48f8028923341d73d00)) - [@tbhb](https://github.com/tbhb)
- add vulture dead code gate (#5) - ([1111c65](https://github.com/proofhouse/proofhouse-python-lib/commit/1111c653f3b5a68f22ddb82acb97c955f805767b)) - [@tbhb](https://github.com/tbhb)
- add complexipy cognitive complexity gate (#4) - ([e4994a6](https://github.com/proofhouse/proofhouse-python-lib/commit/e4994a6c5920472965ffb68b92ae301422440d0b)) - [@tbhb](https://github.com/tbhb)
- add pyrefly strict type checking gate (#2) - ([781b4e5](https://github.com/proofhouse/proofhouse-python-lib/commit/781b4e559c8df7dc5b31a02c0652f1743fe8a725)) - [@tbhb](https://github.com/tbhb)
- wire ruff format and lint with the full ruleset (#1) - ([6e9c571](https://github.com/proofhouse/proofhouse-python-lib/commit/6e9c571574f5e61227065d2653c99f6d0f5544a1)) - [@tbhb](https://github.com/tbhb)
- add self-hosted Renovate config and workflows - ([2cc8265](https://github.com/proofhouse/proofhouse-python-lib/commit/2cc82650d3004cee627bf1f1b9cf0ab683c96a02)) - [@tbhb](https://github.com/tbhb)
- adopt prek with builtin hooks and shared commit-msg gates - ([43c67a5](https://github.com/proofhouse/proofhouse-python-lib/commit/43c67a593a9643a42ca4f938127926796bca2c1a)) - [@tbhb](https://github.com/tbhb)
- add yamllint for YAML linting - ([0ecb351](https://github.com/proofhouse/proofhouse-python-lib/commit/0ecb3514893641bafaf89b4795c5a5164e048147)) - [@tbhb](https://github.com/tbhb)
- add biome for JSON linting and formatting - ([20d53b8](https://github.com/proofhouse/proofhouse-python-lib/commit/20d53b86e29fe950c3f263f186ba1e4d95f84f66)) - [@tbhb](https://github.com/tbhb)
- add rumdl markdown linter - ([26e42f2](https://github.com/proofhouse/proofhouse-python-lib/commit/26e42f28398d49255d9465275daaf7b93c28e260)) - [@tbhb](https://github.com/tbhb)
- add cspell spelling checker with project dictionary - ([ece1515](https://github.com/proofhouse/proofhouse-python-lib/commit/ece15150998df360604019d858e5ff3686bd1584)) - [@tbhb](https://github.com/tbhb)
- add vale prose linter with proofhouse styles and vocabulary - ([ecd6659](https://github.com/proofhouse/proofhouse-python-lib/commit/ecd6659886ecf5ca8ea0822cfc70241cecb0c2b1)) - [@tbhb](https://github.com/tbhb)

#### Style

- shield the vale.ini SPDX example from reuse - ([df8d183](https://github.com/proofhouse/proofhouse-python-lib/commit/df8d18379d0b154131e171da1a8f47b5086d4a51)) - [@tbhb](https://github.com/tbhb)
- apply vale fixes to existing tree - ([1f69a69](https://github.com/proofhouse/proofhouse-python-lib/commit/1f69a69e2e83332d1896c6984b782e8008257a83)) - [@tbhb](https://github.com/tbhb)
