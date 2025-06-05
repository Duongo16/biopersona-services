import os
import subprocess
import datetime
import warnings
import numpy as np
import torchaudio
from fastapi import UploadFile, HTTPException
from speechbrain.inference.speaker import SpeakerRecognition
from bson import ObjectId
from app.db import usercccds_collection

warnings.filterwarnings("ignore", category=FutureWarning)

verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/ecapa"
)

print("Available backends:", torchaudio.list_audio_backends())
print("Current backend:", torchaudio.get_audio_backend())


def convert_webm_to_wav(original_path: str, converted_path: str):
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", original_path, "-ar", "16000", "-ac", "1", converted_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"FFmpeg lỗi: {result.stderr}")


async def process_voice_enroll(user_id: str, file: UploadFile):
    original = f"temp_{user_id}.webm"
    converted = f"converted_{user_id}.wav"

    try:
        with open(original, "wb") as f:
            f.write(await file.read())

        convert_webm_to_wav(original, converted)

        waveform, _ = torchaudio.load(converted)
        embedding = verifier.encode_batch(waveform).squeeze().detach().numpy().tolist()

        user = await usercccds_collection.find_one({"userId": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user.")
        if user.get("faceUrl") is not None:
            await usercccds_collection.update_one(
                {"userId": user_id},
                {"$set": {"voiceVector": embedding, "updatedAt": datetime.datetime.now(), "verified": True}}
            )
        else:
            await usercccds_collection.update_one(
                {"userId": user_id},
                {"$set": {"voiceVector": embedding, "updatedAt": datetime.datetime.now()}}
            )

        

        return {"success": True, "userId": user_id, "vectorDim": len(embedding)}

    finally:
        if os.path.exists(original): os.remove(original)
        if os.path.exists(converted): os.remove(converted)


async def process_voice_verify(user_id: str, file: UploadFile):
    original = f"temp_{user_id}.webm"
    converted = f"converted_{user_id}.wav"

    try:
        with open(original, "wb") as f:
            f.write(await file.read())

        convert_webm_to_wav(original, converted)

        if not os.path.exists(converted):
            raise HTTPException(status_code=500, detail="File WAV không tồn tại.")

        try:
            waveform, _ = torchaudio.load(converted)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi đọc WAV: {str(e)}")
        
        new_vector = verifier.encode_batch(waveform).squeeze().detach().numpy()

        user = await usercccds_collection.find_one({"userId": user_id})
        if not user or "voiceVector" not in user:
            raise HTTPException(status_code=404, detail="Không tìm thấy vector giọng nói.")

        stored_vector = np.array(user["voiceVector"])
        score = float(np.dot(new_vector, stored_vector) / (np.linalg.norm(new_vector) * np.linalg.norm(stored_vector)))
        return {
            "success": True,
            "userId": user_id,
            "score": score,
            "isMatch": score > 0.7
        }

    finally:
        if os.path.exists(original): os.remove(original)
        if os.path.exists(converted): os.remove(converted)
