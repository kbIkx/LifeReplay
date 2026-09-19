package com.kbikx.lifereplay

import com.google.gson.annotations.SerializedName

data class SettingsDto(

    @SerializedName("camera_width")
    val cameraWidth: Int,

    @SerializedName("camera_height")
    val cameraHeight: Int,

    @SerializedName("camera_fps")
    val cameraFps: Int,

    @SerializedName("buffer_seconds")
    val bufferSeconds: Int,

    @SerializedName("pre_seconds")
    val preSeconds: Int,

    @SerializedName("post_seconds")
    val postSeconds: Int,

    @SerializedName("replay_buffer_enabled")
    val replayBufferEnabled: Boolean,

    @SerializedName("auto_delete")
    val autoDelete: Boolean,

    @SerializedName("storage_limit_mb")
    val storageLimitMb: Int
)