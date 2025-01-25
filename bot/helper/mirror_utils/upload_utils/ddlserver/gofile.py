#!/usr/bin/env python3
import os
import shutil
from aiofiles.os import path as aiopath, rename as aiorename
from aiohttp import ClientSession
import requests

class Gofile:
    def __init__(self, dluploader=None):
        self.api_url = "https://api.gofile.io/servers"
        self.dluploader = dluploader

    async def __resp_handler(self, response):
        """Handle API response and raise an exception for unsuccessful responses."""
        api_resp = response.get("status", "")
        if api_resp == "ok":
            return response["data"]
        raise Exception(
            api_resp.split("-")[1]
            if "error-" in api_resp
            else "Response Status is not ok and Reason is Unknown"
        )

    async def __get_server(self):
        """Retrieve the optimal server from Gofile API."""
        async with ClientSession() as session:
            async with session.get('https://api.gofile.io/servers') as resp:
                return await self.__resp_handler(await resp.json())

    async def __compress_folder(self, folder_path):
        """Compress the folder into a zip file."""
        zip_path = f"{folder_path}.zip"
        shutil.make_archive(folder_path, "zip", folder_path)
        return zip_path

    async def upload_file(self, file_path: str):
        """Upload a single file to Gofile."""
        # Format the path to ensure no spaces
        data = requests.get('https://api.gofile.io/servers')
        data = data.json()
        eu_names = [server['name'] for server in data['data']['servers'] if server['zone'] == 'eu']
        new_path = os.path.join(
            os.path.dirname(file_path),
            os.path.basename(file_path).replace(" ", "."),
        )
        await aiorename(file_path, new_path)

        if self.dluploader.is_cancelled:
            return

        upload_url = f"https://{eu_names[0]}.gofile.io/uploadFile"
        req_dict = {}
        upload_file = await self.dluploader.upload_aiohttp(
            upload_url, new_path, "file", req_dict
        )
        return await self.__resp_handler(upload_file)

    async def upload(self, path: str):
        """
        Upload a file or folder to Gofile.

        If the path is a folder, compress it into a zip file before uploading.
        """
        if await aiopath.isdir(path):
            path = await self.__compress_folder(path)

        if await aiopath.isfile(path):
            response = await self.upload_file(path)
            if response.get("downloadPage", False):
                print(response["downloadPage"])
                return response["downloadPage"]

        raise Exception("Failed to upload to Gofile. Please try again later.")
        
