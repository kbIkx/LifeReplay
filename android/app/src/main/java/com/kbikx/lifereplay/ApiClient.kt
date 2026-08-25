package com.kbikx.lifereplay

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {

    private const val BASE_URL =
        "http://192.168.0.15:5000/"

    val api: ReplayApi by lazy {

        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(
                GsonConverterFactory.create()
            )
            .build()
            .create(ReplayApi::class.java)
    }
}