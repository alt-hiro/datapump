from pathlib import Path

from azure.storage.blob import BlobServiceClient


def upload_to_azure_blob(
    connection_string: str, container: str, blob_name: str, file_path: Path
) -> None:
    service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = service_client.get_container_client(container)
    with open(file_path, "rb") as handle:
        container_client.upload_blob(name=blob_name, data=handle, overwrite=True)
