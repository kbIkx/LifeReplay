package com.kbikx.lifereplay

import retrofit2.http.GET

interface ReplayApi {

    @GET("api/replays")
    suspend fun getReplays(): List<ReplayDto>
}