# Tasks

1.  [x] **Create Dockerfile**: Scaffold a `Dockerfile` derived from `python:3.11-slim-bookworm`, installing `[rag]` dependencies and pointing the entry to Iara review tools. Validate the build locally.
2.  [x] **Create Publishing CI**: Introduce `.github/workflows/docker-publish.yml` to build and push the image to GHCR associated with typical release events (or push tags).
3.  [x] **Modify `action.yml`**: Adjust `action.yml` to change `using: 'composite'` over to `using: 'docker'` fetching the image directly from GHCR (`docker://ghcr.io/felipefernandes/iara-bot-reviewer:latest`) providing `args` effectively mapping necessary inputs. Ensure workspace mounting is well-known.
4.  [x] **Update Documentation**: Update `README.md` and other relevant user-facing documents instructing users on how to apply the tool in varied CI environments (GitHub Actions, GitLab CI, Jenkins, Bitbucket) using the Docker image.
5.  [x] **Test execution**: Validate the new `.github/workflows/iara-review.yml` in a distinct Pull Request or branch simulating the pre-built GHCR image.
6.  [x] **Validate & Apply**: Ensure there're no backwards compatibility breaking components and all tests remain functionally successful.
