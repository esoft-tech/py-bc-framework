# For contributing

```{toctree}
:maxdepth: 4
```

## Installing environment

Clone the repository.

```bash
git clone git@github.com:esoft-tech/py-bc-configs.git
```

Install uv using the guide from their website – https://docs.astral.sh/uv/getting-started/installation/.

Inside project directory install dependencies.

```bash
uv sync
```

After that, install pre-commit hook.

```bash
uv run pre-commit install
```

Done 🪄 🐈‍⬛ Now you can develop.

## If you want contributing

- Check that ruff passed.
- Check that mypy passed.
- Before adding or changing the functionality, write unittests.
- Check that unittests passed.

## If you need to build and publish the package

Up the package version in the `pyproject.toml`.

```diff
- version = "0.1.0"
+ version = "0.1.1"
```

Commit changes and push them to the origin.

```bash
git add pyproject.toml
git commit -m "Up to 0.1.1"
git push
```

Make a tag and push them to the origin.

```bash
git tag 0.1.1
git push origin 0.1.1
```

Build the package.

```bash
uv build
```

Publish the package.

```bash
uv publish --token <your-api-token>
```

```{warning}
Make a release with notes about changes.
```

## How to generate badges?

Just exec that command.

```bash
uv run ./.bc/badges.py
```

Then all badges actualize ourselves.

## How to build sphinx docs?

```bash
cd docs && make html
```
