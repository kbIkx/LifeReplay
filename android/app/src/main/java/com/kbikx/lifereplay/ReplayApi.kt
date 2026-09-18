package com.kbikx.lifereplay

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PUT
import retrofit2.http.Path

interface ReplayApi {

    @GET("api/replays")
    suspend fun getReplays(): List<ReplayDto>

    @DELETE("api/replays/{replayId}")
    suspend fun deleteReplay(
        @Path("replayId") replayId: String
    )

    @GET("api/settings")
    suspend fun getSettings(): SettingsDto

    @PUT("api/settings")
    suspend fun updateSettings(
        @Body settings: SettingsDto
    ): SettingsDto
}