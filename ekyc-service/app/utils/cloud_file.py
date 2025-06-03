import base64
import aiohttp

async def file_to_data_uri(file):
    content = await file.read()
    mime = file.content_type
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

async def download_file_from_cloud(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status != 200:
                raise Exception("Không thể tải file từ Cloudinary")
            return await res.read()