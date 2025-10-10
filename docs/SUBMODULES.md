# logicbench_src submodule

URL が判明したら以下を実行:

```bash
git submodule add <REAL_URL> data/logicbench_src
git submodule update --init --recursive
git commit -m "chore: add logicbench_src as submodule"
git push origin main

