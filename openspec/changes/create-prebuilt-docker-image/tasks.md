# Tasks

1.  [ ] **Create Dockerfile**: Scaffold a `Dockerfile` derived from `python:3.11-slim-bookworm`, installing `[rag]` dependencies and pointing the entry to Iara review tools. Validate the build locally.
2.  [ ] **Create Publishing CI**: Introduce `.github/workflows/docker-publish.yml` to build and push the image to GHCR associated with typical release events (or push tags).
3.  [ ] **Modify `action.yml`**: Adjust `action.yml` to change `using: 'composite'` over to `using: 'docker'` fetching the image directly from GHCR (`docker://ghcr.io/gazeus/iara:latest`) providing `args` effectively mapping necessary inputs. Ensure workspace mounting is well-known.
4.  [ ] **Update Documentation**: Update `README.md` and other relevant user-facing documents instructing users on how to apply the tool in varied CI environments (GitHub Actions, GitLab CI, Jenkins, Bitbucket) using the Docker image.
5.  [ ] **Test execution**: Validate the new `.github/workflows/iara-review.yml` in a distinct Pull Request or branch simulating the pre-built GHCR image.
6.  [ ] **Validate & Apply**: Ensure there're no backwards compatibility breaking components and all tests remain functionally successful.
