package com.kbikx.lifereplay

import com.google.gson.annotations.SerializedName

data class ReplayDto(
    val id: String,

    @SerializedName("created_at")
    val createdAt: Double,

    @SerializedName("pre_seconds")
    val preSeconds: Int,

    @SerializedName("post_seconds")
    val postSeconds: Int,

    @SerializedName("frame_count")
    val frameCount: Int,

    @SerializedName("duration_seconds")
    val durationSeconds: Double
)