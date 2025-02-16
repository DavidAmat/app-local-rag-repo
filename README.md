# Installation

## Python installation

```bash
conda_init
conda create --name p_localrag python=3.10.14
conda activate p_localrag
pip install ipykernel
python -m ipykernel install --user --name "kr_localrag"
```

## Repo config

```bash
git remote add origin git@github.com:DavidAmat/app-local-rag-repo.git
git branch -M master
git add .
git commit -m "feat: first commit"
git push -u origin master
```