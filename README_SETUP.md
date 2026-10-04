# AutoVigil setup (on your laptop)

Your base/system Python is never touched. Everything goes in one project environment.

```bash
cd Downloads/AutoVigil          # in Anaconda Prompt (or WSL: /mnt/c/Users/rbsru/Downloads/AutoVigil)
conda env create -f environment.yml
conda activate autovigil
python -m ipykernel install --user --name autovigil --display-name "Python (autovigil)"
```

Remove it after the hackathon if you like: `conda env remove -n autovigil`.
