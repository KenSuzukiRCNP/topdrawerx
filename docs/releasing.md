# Releasing

Where topdrawerx lives, and what to do to cut a release.

## The three places

| | |
| --- | --- |
| **GitHub** — [KenSuzukiRCNP/topdrawerx](https://github.com/KenSuzukiRCNP/topdrawerx) | the source, the issues, and the two workflows. Publishing a *Release* here is what starts everything else. |
| **PyPI** — [topdrawerx](https://pypi.org/project/topdrawerx/) | `pip install topdrawerx`. Uploads happen from GitHub Actions through PyPI's *trusted publishing* (OIDC): there is no API token anywhere, in the repo or on your machine. |
| **Zenodo** — [10.5281/zenodo.22160025](https://doi.org/10.5281/zenodo.22160025) | archives every GitHub Release and mints a DOI, so the code is citable in a paper. |

Two DOIs exist and the difference matters. The **concept DOI**
(`…22160025`) always resolves to the newest version — that is the one in
`CITATION.cff` and the README badge, and it never needs changing. Each release
also gets a **version DOI** (v0.5.1 is `…22160026`); use one of those only when
you must point at one exact version.

The trusted publisher on PyPI is configured with four values that must keep
matching the repository:

    owner        KenSuzukiRCNP
    repository   topdrawerx
    workflow     release.yml
    environment  pypi

## A release, start to finish

1. **Make the change** and get `main` green — `python -m pytest` locally, and
   the `tests` workflow on GitHub across Python 3.10–3.14, Linux and macOS.

2. **Bump the version in three files.** They must agree — `tests/test_version.py`
   fails if they do not, and the release workflow refuses to publish a tag that
   disagrees with `pyproject.toml`. Run the tests *before* tagging: a mismatch
   caught locally costs nothing, a mismatch caught in the workflow has already
   burned a tag and a GitHub Release.

   ```
   pyproject.toml                version = "0.6.0"
   src/topdrawerx/__init__.py    __version__ = "0.6.0"
   CITATION.cff                  version: 0.6.0   and date-released
   ```

3. **Write the CHANGELOG entry** — what changed, and especially anything whose
   *meaning* changed, since the grammar is still 0.x.

4. **Regenerate what is generated**, if the change touched commands or examples:

   ```sh
   python tools/gen_reference.py       # docs/reference.md (a test checks it)
   python tools/render_examples.py     # docs/images for the gallery
   ```

5. **Commit, tag, push.**

   ```sh
   git add -A && git commit -m "topdrawerx 0.6.0: ..."
   git tag -a v0.6.0 -m "topdrawerx 0.6.0"
   git push --follow-tags origin main
   ```

   Pushing a tag publishes nothing on its own — it is only a label.

6. **Publish the GitHub Release.** This is the trigger.

   ```sh
   gh release create v0.6.0 --title "topdrawerx 0.6.0" --notes "..."
   ```

   or Releases → Draft a new release → pick the existing tag → Publish.

7. **Watch Actions.** `release.yml` checks the tag against the version, builds
   the wheel and sdist, runs `twine check`, installs the wheel, actually draws a
   figure with the installed `tdx`, and only then publishes. If the `pypi`
   environment has a required reviewer, the publish job waits for you.

8. **Verify.**

   ```sh
   python -m venv /tmp/t && /tmp/t/bin/pip install topdrawerx && /tmp/t/bin/tdx --version
   ```

   Zenodo picks the release up within a few minutes and adds a version under the
   same concept DOI. Nothing to do by hand.

## Changes that do not need a release

Documentation, the README, CI tweaks: commit and push to `main`. GitHub reads
`CITATION.cff` from the default branch, so a citation fix takes effect
immediately even without a release. PyPI keeps showing the README of the last
*published* version until the next one, which is a fine reason to let small
fixes ride along with the next real release rather than cutting one for them.

## When something goes wrong

**"tag does not match the version"** — the guard did its job. Fix
`pyproject.toml`, or delete and re-cut the tag:

```sh
git tag -d v0.6.0 && git push --delete origin v0.6.0
```

**The publish step is rejected by PyPI** — the four trusted-publisher values
above have drifted from the repository; check the workflow *file name* first,
it is the one that catches people.

**A version was published by mistake** — PyPI does not allow re-uploading a
version, even after deleting it. Bump the patch number and release again.

**A stray local tag** — `git tag -d <name>`. Lightweight tags are not pushed by
`--follow-tags`, so they usually never left your machine.
