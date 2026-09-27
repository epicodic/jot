# Contributing

## Development setup

You need [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/epicodic/jot
cd jot
uv sync --all-groups
uv run jot            # run from source
```

Before you open a pull request, run the QA script. It formats the code in place,
then runs the linter, the type checker, and the tests, which are the same checks
CI runs:

```sh
./qa.sh
```

## Updating the screenshots

`docs/screenshot*.svg` are Textual SVG exports. To regenerate them, drive the app
headlessly with `JotApp.run_test()` and call `app.save_screenshot(path="docs")`.

## Releasing

Releases are published to [PyPI](https://pypi.org/project/jot-editor/) by the
[`Publish`](.github/workflows/publish.yml) workflow using
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API tokens
are stored in the repository.

1. Bump the version: `uv version --bump minor` (or `patch` / `major`).
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version.
3. Commit, tag, and push:

   ```sh
   git commit -am "release: v$(uv version --short)"
   git tag "v$(uv version --short)"
   git push origin main --tags
   ```

The workflow runs CI and checks that the tag matches the `pyproject.toml`
version. It then builds the package, uploads it to PyPI, and creates a GitHub
release with the built files attached.

### One-time setup

Do this once, before the first release:

1. On PyPI, go to **Your projects → Publishing → Add a new pending publisher**
   and enter:
   - PyPI project name: `jot-editor`
   - Owner: `epicodic`, Repository: `jot`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. In the GitHub repository, go to **Settings → Environments** and create the
   environment `pypi`. It's a good idea to add yourself as a required
   reviewer, so every release waits for a manual approval.
