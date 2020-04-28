import os
import pandas as pd
from io import BytesIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

class StorageConnector:
    """Meta Storage Connector used to retrieve and send file in cloud storages
    Cloud Provider Agnostic
    # PART OF WBUTILS

    Raises:
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]
        NotImplementedError: [description]

    Returns:
        [type]: [description]
    """
    CLOUD_PROVIDER = None

    def __init__(self, credentials, storage_name, **args):
        """Instantiate the connector

        Args:
            credentials ([type]): Needed credentials
            storage_name ([type]): Container/Bucket name
        """
        self.storage_name = storage_name
        self._conn = None

    def update_storage(self, storage_name: str):
        """Update the container/bucket name

        Args:
            storage_name (str): Container/Bucket name
        """
        self.storage_name = storage_name

    def is_file(self, filepath: str) -> bool:
        """Check whether or not the `filepath` is a genuine file in storage

        Args:
            filepath (str): File name in storage

        Raises:
            NotImplementedError: [description]

        Returns:
            bool: [description]
        """
        raise NotImplementedError

    def list_files(self, prefix: str = "") -> list:
        """List all the files in storage with a prefix

        Args:
            prefix (str, optional): Prefix to use to limit listed files. Defaults to "".

        Raises:
            NotImplementedError: [description]

        Returns:
            list: List of file names as strings
        """
        raise NotImplementedError

    def fetch_file(self, filepath: str) -> bytes:
        """Retrieve file from storage as bytes

        Args:
            filepath (str): File name to retrieve

        Raises:
            NotImplementedError: [description]

        Returns:
            bytes: Downloaded file as bytes
        """
        raise NotImplementedError

    def open_as_dataframe(self, filepath: str, **args) -> pd.DataFrame:
        """Retrieve file from storage as pandas DataFrame

        Args:
            filepath (str): File name to retrieve

        Raises:
            NotImplementedError: [description]

        Returns:
            pd.DataFrame: Downloaded file as dataframe
        """
        raise NotImplementedError

    def send_file(self, filepath: str, cloudpath):
        """Upload local file to storage

        Args:
            filepath (str): File to upload
            cloudpath ([type]): Storage location

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def send_data(self, buff: str, cloudpath):
        """Upload buffer to storage

        Args:
            buff (str): String buffer
            cloudpath ([type]): Storage location

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def get_last_filename_version(self, fileformat:str) -> str:
        """Returns max operator of `list_files`methods
        
        Note:
            This method is mostly used to retrieve the last version of a file.
            To do so, file names in storage should follow this naming convention:
            `<GENERIC_FILE_NAME>_<YYYY>-<MM>-<DD>.*`

        Args:
            fileformat (str): Generic file name to look for

        Returns:
            str: Most recent file in storage following the generic name
        """
        file_list = self.list_files(prefix=fileformat)
        return max(file_list)


class AzureBlobConnector(StorageConnector):
    """Storage Connector for Azure Storage Account

    Raises:
        Exception: [description]
        FileNotFoundError: [description]
    """
    CLOUD_PROVIDER = "AZURE"

    def __init__(self, credentials:str, storage_name:str, **args):
        """Instantiate the Azure Storage Connector

        Args:
            credentials (str): Connection string
            storage_name (str): Container name
        """
        super(AzureBlobConnector, self).__init__(credentials, storage_name, **args)
        self._conn_service = BlobServiceClient.from_connection_string(credentials)
        self.update_storage(storage_name=storage_name)

    def _is_container(self, container_name:str) -> bool:
        """Check whether or not `container_name` is a genuine container

        Args:
            container_name (str): Container name

        Returns:
            bool: Whether or not `container_name` is a genuine container
        """
        return container_name in [
            container["name"]
            for container in list(self._conn_service.list_containers())
        ]
    
    def update_storage(self, storage_name: str):
        """Update the container to use by the Connector

        Args:
            storage_name (str): New Container name

        Raises:
            Exception: The new Container name is not a genuine Blob container
        """
        if self._is_container(storage_name):
            self._conn = self._conn_service.get_container_client(storage_name)
            self.storage_name = storage_name
        else:
            raise Exception(
                f"<{self.storage_name}> does not exist in the defined Blob Service"
            )

    def list_files(self, prefix: str = "") -> list:
        """List all the files in storage with a prefix

        Args:
            prefix (str, optional): Prefix to use to limit listed files. Defaults to "".

        Returns:
            list: List of file names as strings
        """
        return [blob["name"] for blob in list(self._conn.list_blobs(prefix))]

    def is_file(self, filepath: str) -> bool:
        """Check whether or not the `filepath` is a genuine file in storage

        Args:
            filepath (str): File name in storage

        Returns:
            bool: Whether or not the `filepath` is a genuine file
        """
        return len(self.list_files(filepath)) > 0

    def open_as_dataframe(self, filepath: str, **args) -> pd.DataFrame:
        """Retrieve file from storage as pandas DataFrame

        Args:
            filepath (str): File name to retrieve

        Returns:
            pd.DataFrame: Downloaded file as dataframe
        """
        b = self.fetch_file(filepath)
        buff = BytesIO(b)
        df = pd.read_csv(buff, **args)
        return df
        
    def fetch_file(self, filepath: str) -> bytes:
        """Retrieve file from storage as bytes

        Args:
            filepath (str): File name to retrieve

        Raises:
            FileNotFoundError: File dos not exist in storage

        Returns:
            bytes: Downloaded file as bytes
        """
        if self.is_file(filepath):
            return self._conn.download_blob(filepath).content_as_bytes()
        else:
            raise FileNotFoundError(f'{filepath} was not found in Blob Container <{self.storage_name}>')
    
    def send_file(self, filepath: str, cloudpath:str):
        """Upload local file to storage

        Args:
            filepath (str): File to upload
            cloudpath ([type]): Storage location
        """
        # Upload content to block blob
        with open(filepath, "rb") as data:
            self._conn.get_blob_client(cloudpath).upload_blob(data, blob_type="BlockBlob")
    
    def send_data(self, buff: str, cloudpath:str):
        """Upload buffer to storage

        Args:
            buff (str): String buffer
            cloudpath ([type]): Storage location
        """
        # Upload content to block blob
        self._conn.get_blob_client(cloudpath).upload_blob(buff, blob_type="BlockBlob")



    
