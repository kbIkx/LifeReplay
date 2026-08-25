package com.kbikx.lifereplay

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.kbikx.lifereplay.ui.theme.LifeReplayTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(
        savedInstanceState: Bundle?
    ) {
        super.onCreate(savedInstanceState)

        setContent {
            LifeReplayTheme {
                ReplayScreen()
            }
        }
    }
}

@androidx.compose.runtime.Composable
fun ReplayScreen() {

    var replays by remember {
        mutableStateOf<List<ReplayDto>>(emptyList())
    }

    var loading by remember {
        mutableStateOf(true)
    }

    var error by remember {
        mutableStateOf<String?>(null)
    }

    LaunchedEffect(Unit) {

        try {
            replays = ApiClient.api.getReplays()
        } catch (exception: Exception) {
            error = exception.toString()
        } finally {
            loading = false
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),

        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {

        Text(
            text = "LifeReplay",
            style = MaterialTheme.typography.headlineMedium
        )

        when {

            loading -> {
                CircularProgressIndicator()
            }

            error != null -> {
                Text(
                    text = "Ошибка:\n$error",
                    color = MaterialTheme.colorScheme.error
                )
            }

            replays.isEmpty() -> {
                Text(
                    text = "Replay не найдены"
                )
            }

            else -> {
                LazyColumn(
                    verticalArrangement =
                        Arrangement.spacedBy(8.dp)
                ) {

                    items(
                        items = replays,
                        key = { it.id }
                    ) { replay ->

                        Card {

                            Column(
                                modifier = Modifier
                                    .padding(16.dp)
                            ) {

                                Text(
                                    text =
                                        "Replay ${replay.id}"
                                )

                                Text(
                                    text =
                                        "Длительность: " +
                                                "${replay.durationSeconds} сек"
                                )

                                Text(
                                    text =
                                        "Кадров: " +
                                                "${replay.frameCount}"
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}