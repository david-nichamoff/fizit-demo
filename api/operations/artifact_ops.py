import requests

class ArtifactOperations:
    def __init__(self, headers, config):
        self.headers = headers
        self.config = config

    def get_artifacts(self, contract_idx):
        """Retrieve a list of artifacts associated with a contract."""
        response = requests.get(
            f"{self.config['url']}/api/contracts/{contract_idx}/artifacts/",
            headers=self.headers
        )
        return response

    def add_artifacts(self, contract_idx, artifact_urls, csrf_token):
        """Add artifacts to a contract."""
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token

        # Send the request to add artifacts. The artifact_urls should contain the URL(s) of the artifact(s).
        response = requests.post(
            f"{self.config['url']}/api/contracts/{contract_idx}/artifacts/",
            headers=headers_with_csrf,
            json={"artifact_urls": artifact_urls},
            cookies={'csrftoken': csrf_token}
        )
        return response

    def delete_artifacts(self, contract_idx, csrf_token):
        """Delete all artifacts associated with a contract."""
        headers_with_csrf = self.headers.copy()
        headers_with_csrf['X-CSRFToken'] = csrf_token

        response = requests.delete(
            f"{self.config['url']}/api/contracts/{contract_idx}/artifacts/",
            headers=headers_with_csrf,
            cookies={'csrftoken': csrf_token}
        )
        return response