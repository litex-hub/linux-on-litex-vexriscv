# Install Conda

Full instructions for installing conda are found in the
[Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

## Linux

```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O Miniconda3-latest-Linux-x86_64.sh
chmod a+x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -p env -b -f
```

# Create the `linux-on-litex-vexriscv` environment

```
conda env create --file environment.yml
```

# Enter environment

```
conda activate linux-on-litex-vexriscv
```

# Run build
```
./make.py --board=<your board>
```
