package com.kbikx.lifereplay

import android.content.ContentValues
import android.graphics.BitmapFactory
import android.os.Bundle
import android.provider.MediaStore
import android.widget.ImageView
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.kbikx.lifereplay.ui.theme.LifeReplayTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            LifeReplayTheme {
                LifeReplayApp()
            }
        }
    }
}

@Composable
fun LifeReplayApp() {

    var selectedReplay by remember {
        mutableStateOf<ReplayDto?>(null)
    }

    var showSettings by remember {
        mutableStateOf(false)
    }

    when {
        selectedReplay != null -> {
            VideoPlayerScreen(
                replay = selectedReplay!!,
                onBack = {
                    selectedReplay = null
                }
            )
        }

        showSettings -> {
            SettingsScreen(
                onBack = {
                    showSettings = false
                }
            )
        }

        else -> {
            HomeScreen(
                onWatchReplay = { replay ->
                    selectedReplay = replay
                },
                onOpenSettings = {
                    showSettings = true
                }
            )
        }
    }
}

@Composable
fun HomeScreen(
    onWatchReplay: (ReplayDto) -> Unit,
    onOpenSettings: () -> Unit
) {
    var replays by remember {
        mutableStateOf<List<ReplayDto>>(emptyList())
    }

    var loading by remember {
        mutableStateOf(true)
    }

    var refreshing by remember {
        mutableStateOf(false)
    }

    var error by remember {
        mutableStateOf<String?>(null)
    }

    var deletingReplayId by remember {
        mutableStateOf<String?>(null)
    }

    var replayToDelete by remember {
        mutableStateOf<ReplayDto?>(null)
    }

    val scope = rememberCoroutineScope()

    suspend fun loadReplays(fullLoading: Boolean) {
        try {
            if (fullLoading) {
                loading = true
            } else {
                refreshing = true
            }

            error = null
            replays = ApiClient.api.getReplays()

        } catch (exception: Exception) {
            exception.printStackTrace()

            error =
                "${exception.javaClass.simpleName}: ${exception.message}"

        } finally {
            loading = false
            refreshing = false
        }
    }

    LaunchedEffect(Unit) {
        loadReplays(true)
    }

    if (replayToDelete != null) {
        AlertDialog(
            onDismissRequest = {
                replayToDelete = null
            },

            title = {
                Text("Удалить Replay?")
            },

            text = {
                Text(
                    "Эта запись будет удалена без возможности восстановления."
                )
            },

            confirmButton = {
                TextButton(
                    onClick = {
                        val replay = replayToDelete
                        replayToDelete = null

                        if (replay != null) {
                            scope.launch {
                                deletingReplayId = replay.id

                                try {
                                    ApiClient.api.deleteReplay(replay.id)

                                    replays =
                                        replays.filter {
                                            it.id != replay.id
                                        }

                                } catch (exception: Exception) {
                                    exception.printStackTrace()

                                    error =
                                        "${exception.javaClass.simpleName}: " +
                                                "${exception.message}"

                                } finally {
                                    deletingReplayId = null
                                }
                            }
                        }
                    }
                ) {
                    Text(
                        text = "Удалить",
                        color = MaterialTheme.colorScheme.error
                    )
                }
            },

            dismissButton = {
                TextButton(
                    onClick = {
                        replayToDelete = null
                    }
                ) {
                    Text("Отмена")
                }
            }
        )
    }

    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .padding(16.dp),

        verticalArrangement =
            Arrangement.spacedBy(16.dp)
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {

            Column(
                modifier = Modifier.weight(1f)
            ) {

                Text(
                    text = "LifeReplay",
                    fontSize = 30.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text = "Smart Replay Camera",
                    fontSize = 13.sp,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            TextButton(
                onClick = onOpenSettings
            ) {
                Text(
                    text = "⚙",
                    fontSize = 27.sp
                )
            }
        }

        StatusCard()

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {

            Column(
                modifier = Modifier.weight(1f)
            ) {

                Text(
                    text = "Последние записи",
                    fontSize = 21.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text =
                        when {
                            loading -> "Загрузка..."
                            replays.isEmpty() ->
                                "Нет сохранённых записей"
                            else ->
                                "${replays.size} записей"
                        },

                    fontSize = 13.sp,

                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            TextButton(
                onClick = {
                    scope.launch {
                        loadReplays(false)
                    }
                },

                enabled =
                    !loading && !refreshing
            ) {

                if (refreshing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp
                    )
                } else {
                    Text(
                        text = "↻",
                        fontSize = 22.sp
                    )
                }
            }
        }

        if (error != null) {

            Card(
                modifier = Modifier.fillMaxWidth(),

                shape =
                    RoundedCornerShape(16.dp),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme.colorScheme.errorContainer
                    )
            ) {

                Column(
                    modifier = Modifier.padding(16.dp)
                ) {

                    Text(
                        text = "Ошибка подключения",
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(
                        modifier = Modifier.height(5.dp)
                    )

                    Text(
                        text = error!!,
                        fontSize = 12.sp
                    )
                }
            }
        }

        if (loading) {

            Box(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(300.dp),

                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }

        } else if (replays.isEmpty()) {

            EmptyState()

        } else {

            LazyColumn(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .weight(1f),

                verticalArrangement =
                    Arrangement.spacedBy(12.dp)
            ) {

                items(
                    items = replays,
                    key = { it.id }
                ) { replay ->

                    ReplayCard(
                        replay = replay,

                        deleting =
                            deletingReplayId == replay.id,

                        onWatch = {
                            onWatchReplay(replay)
                        },

                        onDelete = {
                            replayToDelete = replay
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun StatusCard() {

    Card(
        modifier = Modifier.fillMaxWidth(),

        shape =
            RoundedCornerShape(22.dp),

        colors =
            CardDefaults.cardColors(
                containerColor =
                    MaterialTheme.colorScheme.surfaceVariant
            )
    ) {

        Column(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(20.dp),

            horizontalAlignment =
                Alignment.CenterHorizontally,

            verticalArrangement =
                Arrangement.spacedBy(12.dp)
        ) {

            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {

                Box(
                    modifier =
                        Modifier
                            .size(10.dp)
                            .clip(CircleShape)
                            .background(
                                Color(0xFF4CAF50)
                            )
                )

                Spacer(
                    modifier = Modifier.width(7.dp)
                )

                Text(
                    text = "CAMERA ONLINE",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF4CAF50)
                )
            }

            Text(
                text = "REPLAY BUFFER",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )

            Button(
                onClick = {
                    // TODO:
                    // Подключить настоящий rollback API.
                },

                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(65.dp),

                shape =
                    RoundedCornerShape(18.dp),

                colors =
                    ButtonDefaults.buttonColors(
                        containerColor =
                            Color(0xFFE53935)
                    )
            ) {

                Text(
                    text = "●  ROLLBACK",
                    fontSize = 19.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Text(
                text = "Сохранить последние секунды видео",

                fontSize = 12.sp,

                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun SettingsScreen(
    onBack: () -> Unit
) {

    val scope = rememberCoroutineScope()

    var settings by remember {
        mutableStateOf<SettingsDto?>(null)
    }

    var loading by remember {
        mutableStateOf(true)
    }

    var saving by remember {
        mutableStateOf(false)
    }

    var error by remember {
        mutableStateOf<String?>(null)
    }

    var saved by remember {
        mutableStateOf(false)
    }

    LaunchedEffect(Unit) {

        try {
            error = null
            settings = ApiClient.api.getSettings()

        } catch (exception: Exception) {

            exception.printStackTrace()

            error =
                "${exception.javaClass.simpleName}: " +
                        "${exception.message}"

        } finally {
            loading = false
        }
    }

    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .padding(16.dp)
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {

            TextButton(
                onClick = onBack
            ) {
                Text(
                    text = "‹ Назад",
                    fontSize = 18.sp
                )
            }

            Text(
                text = "Настройки",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(start = 4.dp)
            )
        }

        Spacer(
            modifier = Modifier.height(10.dp)
        )

        if (loading) {

            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }

            return@Column
        }

        if (error != null) {

            Card(
                modifier = Modifier.fillMaxWidth(),

                shape =
                    RoundedCornerShape(16.dp),

                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            MaterialTheme.colorScheme.errorContainer
                    )
            ) {

                Column(
                    modifier = Modifier.padding(16.dp)
                ) {

                    Text(
                        text = "Не удалось загрузить настройки",
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(
                        modifier = Modifier.height(6.dp)
                    )

                    Text(
                        text = error!!,
                        fontSize = 12.sp
                    )

                    Spacer(
                        modifier = Modifier.height(12.dp)
                    )

                    Button(
                        onClick = {
                            scope.launch {
                                try {
                                    error = null
                                    loading = true
                                    settings =
                                        ApiClient.api.getSettings()
                                } catch (exception: Exception) {
                                    error =
                                        "${exception.javaClass.simpleName}: " +
                                                "${exception.message}"
                                } finally {
                                    loading = false
                                }
                            }
                        }
                    ) {
                        Text("Повторить")
                    }
                }
            }

            return@Column
        }

        val currentSettings =
            settings ?: return@Column

        LazyColumn(
            modifier = Modifier.weight(1f),

            verticalArrangement =
                Arrangement.spacedBy(12.dp)
        ) {

            item {
                SettingsSectionTitle(
                    title = "Replay"
                )
            }

            item {

                SettingSwitchCard(
                    title = "Replay Buffer",

                    description =
                        "Фоновая запись последних секунд видео",

                    checked =
                        currentSettings.replayBufferEnabled,

                    onCheckedChange = { checked ->

                        settings =
                            currentSettings.copy(
                                replayBufferEnabled = checked
                            )

                        saved = false
                    }
                )
            }

            item {

                SecondsSettingCard(
                    title = "PRE-event",

                    description =
                        "Сколько секунд сохранить до нажатия кнопки",

                    value =
                        currentSettings.preSeconds,

                    min = 0,

                    max =
                        currentSettings.bufferSeconds,

                    onValueChange = { value ->

                        settings =
                            currentSettings.copy(
                                preSeconds = value
                            )

                        saved = false
                    }
                )
            }

            item {

                SecondsSettingCard(
                    title = "POST-event",

                    description =
                        "Сколько секунд записывать после нажатия",

                    value =
                        currentSettings.postSeconds,

                    min = 0,

                    max = 10,

                    onValueChange = { value ->

                        settings =
                            currentSettings.copy(
                                postSeconds = value
                            )

                        saved = false
                    }
                )
            }

            item {

                SettingsSectionTitle(
                    title = "Camera"
                )
            }

            item {

                ResolutionSettingCard(
                    width =
                        currentSettings.cameraWidth,

                    height =
                        currentSettings.cameraHeight,

                    onResolutionChange = { width, height ->

                        val supportedFps =
                            getSupportedFps(width)

                        val newFps =
                            if (
                                currentSettings.cameraFps
                                in supportedFps
                            ) {
                                currentSettings.cameraFps
                            } else {
                                supportedFps.last()
                            }

                        settings =
                            currentSettings.copy(
                                cameraWidth = width,
                                cameraHeight = height,
                                cameraFps = newFps
                            )

                        saved = false
                    }
                )
            }

            item {

                FpsSettingCard(
                    fps =
                        currentSettings.cameraFps,

                    availableFps =
                        getSupportedFps(
                            currentSettings.cameraWidth
                        ),

                    onFpsChange = { fps ->

                        settings =
                            currentSettings.copy(
                                cameraFps = fps
                            )

                        saved = false
                    }
                )
            }

            item {

                SettingsSectionTitle(
                    title = "Storage"
                )
            }

            item {

                SettingSwitchCard(
                    title = "Auto Delete",

                    description =
                        "Автоматически удалять старые записи",

                    checked =
                        currentSettings.autoDelete,

                    onCheckedChange = { checked ->

                        settings =
                            currentSettings.copy(
                                autoDelete = checked
                            )

                        saved = false
                    }
                )
            }

            item {

                StorageLimitCard(
                    value =
                        currentSettings.storageLimitMb,

                    onValueChange = { value ->

                        settings =
                            currentSettings.copy(
                                storageLimitMb = value
                            )

                        saved = false
                    }
                )
            }

            item {

                Spacer(
                    modifier = Modifier.height(4.dp)
                )

                Button(
                    onClick = {

                        scope.launch {

                            try {

                                saving = true
                                error = null

                                val updated =
                                    ApiClient.api.updateSettings(
                                        currentSettings
                                    )

                                settings = updated
                                saved = true

                            } catch (exception: Exception) {

                                exception.printStackTrace()

                                error =
                                    "${exception.javaClass.simpleName}: " +
                                            "${exception.message}"

                                saved = false

                            } finally {
                                saving = false
                            }
                        }
                    },

                    enabled = !saving,

                    modifier =
                        Modifier
                            .fillMaxWidth()
                            .height(55.dp),

                    shape =
                        RoundedCornerShape(16.dp)
                ) {

                    if (saving) {

                        CircularProgressIndicator(
                            modifier =
                                Modifier.size(22.dp),
                            strokeWidth = 2.dp
                        )

                    } else {

                        Text(
                            text =
                                if (saved) {
                                    "✓ Сохранено"
                                } else {
                                    "Сохранить настройки"
                                },

                            fontSize = 16.sp,

                            fontWeight =
                                FontWeight.Bold
                        )
                    }
                }

                if (error != null) {

                    Spacer(
                        modifier = Modifier.height(8.dp)
                    )

                    Text(
                        text = error!!,
                        fontSize = 12.sp,
                        color =
                            MaterialTheme.colorScheme.error
                    )
                }

                Spacer(
                    modifier = Modifier.height(20.dp)
                )
            }
        }
    }
}

@Composable
fun SettingsSectionTitle(
    title: String
) {

    Text(
        text = title.uppercase(),
        fontSize = 13.sp,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,

        modifier =
            Modifier.padding(
                top = 8.dp,
                bottom = 2.dp
            )
    )
}

@Composable
fun SettingSwitchCard(
    title: String,
    description: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp)
    ) {

        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(16.dp),

            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Column(
                modifier =
                    Modifier.weight(1f)
            ) {

                Text(
                    text = title,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(
                    modifier = Modifier.height(3.dp)
                )

                Text(
                    text = description,
                    fontSize = 12.sp,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange
            )
        }
    }
}

@Composable
fun SecondsSettingCard(
    title: String,
    description: String,
    value: Int,
    min: Int,
    max: Int,
    onValueChange: (Int) -> Unit
) {

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp)
    ) {

        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(16.dp),

            verticalAlignment =
                Alignment.CenterVertically
        ) {

            Column(
                modifier =
                    Modifier.weight(1f)
            ) {

                Text(
                    text = title,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )

                Spacer(
                    modifier = Modifier.height(3.dp)
                )

                Text(
                    text = description,
                    fontSize = 12.sp,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Row(
                verticalAlignment =
                    Alignment.CenterVertically
            ) {

                OutlinedButton(
                    onClick = {
                        onValueChange(
                            (value - 1).coerceAtLeast(min)
                        )
                    },

                    enabled = value > min,

                    modifier =
                        Modifier.size(42.dp),

                    contentPadding =
                        PaddingValues(0.dp),

                    shape =
                        RoundedCornerShape(12.dp)
                ) {

                    Text(
                        text = "−",
                        fontSize = 20.sp
                    )
                }

                Text(
                    text = "$value с",

                    modifier =
                        Modifier.width(55.dp),

                    textAlign =
                        TextAlign.Center,

                    fontWeight =
                        FontWeight.Bold
                )

                OutlinedButton(
                    onClick = {
                        onValueChange(
                            (value + 1).coerceAtMost(max)
                        )
                    },

                    enabled = value < max,

                    modifier =
                        Modifier.size(42.dp),

                    contentPadding =
                        PaddingValues(0.dp),

                    shape =
                        RoundedCornerShape(12.dp)
                ) {

                    Text(
                        text = "+",
                        fontSize = 20.sp
                    )
                }
            }
        }
    }
}

@Composable
fun ResolutionSettingCard(
    width: Int,
    height: Int,
    onResolutionChange: (Int, Int) -> Unit
) {

    var expanded by remember {
        mutableStateOf(false)
    }

    val resolutions =
        listOf(
            640 to 480,
            1296 to 972,
            1920 to 1080,
            2592 to 1944
        )

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp)
    ) {

        Column(
            modifier = Modifier.padding(16.dp)
        ) {

            Text(
                text = "Resolution",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(
                modifier = Modifier.height(3.dp)
            )

            Text(
                text = "Разрешение камеры",
                fontSize = 12.sp,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            Box {

                OutlinedButton(
                    onClick = {
                        expanded = true
                    },

                    modifier =
                        Modifier.fillMaxWidth(),

                    shape =
                        RoundedCornerShape(12.dp)
                ) {

                    Row(
                        modifier =
                            Modifier.fillMaxWidth(),

                        horizontalArrangement =
                            Arrangement.SpaceBetween
                    ) {

                        Text(
                            text = "$width × $height"
                        )

                        Text("▼")
                    }
                }

                DropdownMenu(
                    expanded = expanded,

                    onDismissRequest = {
                        expanded = false
                    }
                ) {

                    resolutions.forEach { resolution ->

                        val selected =
                            resolution.first == width &&
                                    resolution.second == height

                        DropdownMenuItem(

                            text = {

                                Text(
                                    text =
                                        "${resolution.first} × " +
                                                "${resolution.second}"
                                )
                            },

                            onClick = {

                                onResolutionChange(
                                    resolution.first,
                                    resolution.second
                                )

                                expanded = false
                            },

                            trailingIcon = {

                                if (selected) {
                                    Text("✓")
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun FpsSettingCard(
    fps: Int,
    availableFps: List<Int>,
    onFpsChange: (Int) -> Unit
) {

    var expanded by remember {
        mutableStateOf(false)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp)
    ) {

        Column(
            modifier = Modifier.padding(16.dp)
        ) {

            Text(
                text = "FPS",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(
                modifier = Modifier.height(3.dp)
            )

            Text(
                text = "Частота кадров",
                fontSize = 12.sp,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            Box {

                OutlinedButton(
                    onClick = {
                        expanded = true
                    },

                    modifier =
                        Modifier.fillMaxWidth(),

                    shape =
                        RoundedCornerShape(12.dp)
                ) {

                    Row(
                        modifier =
                            Modifier.fillMaxWidth(),

                        horizontalArrangement =
                            Arrangement.SpaceBetween
                    ) {

                        Text(
                            text = "$fps FPS"
                        )

                        Text("▼")
                    }
                }

                DropdownMenu(
                    expanded = expanded,

                    onDismissRequest = {
                        expanded = false
                    }
                ) {

                    availableFps.forEach { available ->

                        DropdownMenuItem(

                            text = {
                                Text("$available FPS")
                            },

                            onClick = {

                                onFpsChange(available)
                                expanded = false
                            },

                            trailingIcon = {

                                if (available == fps) {
                                    Text("✓")
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun StorageLimitCard(
    value: Int,
    onValueChange: (Int) -> Unit
) {

    var expanded by remember {
        mutableStateOf(false)
    }

    val limits =
        listOf(
            100,
            512,
            1024,
            2048,
            4096
        )

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp)
    ) {

        Column(
            modifier = Modifier.padding(16.dp)
        ) {

            Text(
                text = "Storage Limit",
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(
                modifier = Modifier.height(3.dp)
            )

            Text(
                text =
                    "Максимальный размер хранилища для Replay",

                fontSize = 12.sp,

                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            Box {

                OutlinedButton(
                    onClick = {
                        expanded = true
                    },

                    modifier =
                        Modifier.fillMaxWidth(),

                    shape =
                        RoundedCornerShape(12.dp)
                ) {

                    Row(
                        modifier =
                            Modifier.fillMaxWidth(),

                        horizontalArrangement =
                            Arrangement.SpaceBetween
                    ) {

                        Text(
                            text =
                                formatStorageLimit(value)
                        )

                        Text("▼")
                    }
                }

                DropdownMenu(
                    expanded = expanded,

                    onDismissRequest = {
                        expanded = false
                    }
                ) {

                    limits.forEach { limit ->

                        DropdownMenuItem(

                            text = {
                                Text(
                                    formatStorageLimit(limit)
                                )
                            },

                            onClick = {

                                onValueChange(limit)
                                expanded = false
                            },

                            trailingIcon = {

                                if (limit == value) {
                                    Text("✓")
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

fun getSupportedFps(
    width: Int
): List<Int> {

    return when (width) {

        640 -> listOf(15, 30, 60)

        1296 -> listOf(15, 24, 30)

        1920 -> listOf(15, 24, 30)

        2592 -> listOf(15)

        else -> listOf(30)
    }
}

fun formatStorageLimit(
    megabytes: Int
): String {

    return if (megabytes >= 1024) {

        val gigabytes =
            megabytes / 1024

        "$gigabytes GB"

    } else {

        "$megabytes MB"
    }
}

@Composable
fun ReplayCard(
    replay: ReplayDto,
    deleting: Boolean,
    onWatch: () -> Unit,
    onDelete: () -> Unit
) {

    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val thumbnailUrl =
        "http://192.168.0.16:5000/" +
                "api/replays/${replay.id}/thumbnail"

    var downloading by remember(replay.id) {
        mutableStateOf(false)
    }

    var downloadProgress by remember(replay.id) {
        mutableIntStateOf(0)
    }

    var downloaded by remember(replay.id) {
        mutableStateOf(false)
    }

    var downloadError by remember(replay.id) {
        mutableStateOf<String?>(null)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),

        shape =
            RoundedCornerShape(20.dp),

        elevation =
            CardDefaults.cardElevation(
                defaultElevation = 3.dp
            )
    ) {

        Column {

            Box(
                modifier =
                    Modifier
                        .fillMaxWidth()
                        .height(185.dp)
                        .clickable(
                            enabled =
                                !deleting &&
                                        !downloading
                        ) {
                            onWatch()
                        }
            ) {

                ReplayThumbnail(
                    url = thumbnailUrl
                )

                Box(
                    modifier =
                        Modifier
                            .align(Alignment.Center)
                            .size(54.dp)
                            .clip(CircleShape)
                            .background(
                                Color.Black.copy(
                                    alpha = 0.65f
                                )
                            ),

                    contentAlignment =
                        Alignment.Center
                ) {

                    Text(
                        text = "▶",
                        color = Color.White,
                        fontSize = 24.sp
                    )
                }
            }

            Column(
                modifier = Modifier.padding(14.dp),

                verticalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {

                    Column(
                        modifier =
                            Modifier.weight(1f)
                    ) {

                        Text(
                            text =
                                formatReplayDate(
                                    replay.createdAt
                                ),

                            fontSize = 16.sp,

                            fontWeight =
                                FontWeight.Bold
                        )

                        Spacer(
                            modifier = Modifier.height(2.dp)
                        )

                        Text(
                            text =
                                "${formatDuration(replay.durationSeconds)}  •  " +
                                        formatFileSize(replay.fileSizeBytes),

                            fontSize = 12.sp,

                            color =
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                if (downloadError != null) {

                    Text(
                        text =
                            "Ошибка скачивания: $downloadError",

                        fontSize = 12.sp,

                        color =
                            MaterialTheme.colorScheme.error
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement =
                        Arrangement.spacedBy(8.dp)
                ) {

                    Button(
                        onClick = onWatch,

                        enabled =
                            !deleting &&
                                    !downloading,

                        modifier =
                            Modifier.weight(1.2f),

                        contentPadding =
                            PaddingValues(
                                horizontal = 8.dp
                            ),

                        shape =
                            RoundedCornerShape(12.dp)
                    ) {

                        Text(
                            text = "▶ Смотреть",
                            fontSize = 13.sp
                        )
                    }

                    OutlinedButton(
                        onClick = {

                            if (downloading) {
                                return@OutlinedButton
                            }

                            downloading = true
                            downloadProgress = 0
                            downloaded = false
                            downloadError = null

                            scope.launch {

                                val result =
                                    downloadReplayToGallery(
                                        context = context,
                                        replay = replay,
                                        onProgress = { progress ->
                                            downloadProgress =
                                                progress
                                        }
                                    )

                                downloading = false

                                result
                                    .onSuccess {
                                        downloaded = true
                                        downloadProgress = 100
                                    }
                                    .onFailure { exception ->
                                        downloadError =
                                            exception.message
                                                ?: "Неизвестная ошибка"
                                    }
                            }
                        },

                        enabled =
                            !deleting &&
                                    !downloading &&
                                    !downloaded,

                        modifier =
                            Modifier.weight(1f),

                        contentPadding =
                            PaddingValues(
                                horizontal = 8.dp
                            ),

                        shape =
                            RoundedCornerShape(12.dp)
                    ) {

                        when {

                            downloading -> {
                                Text(
                                    text =
                                        "$downloadProgress%",
                                    fontSize = 13.sp
                                )
                            }

                            downloaded -> {
                                Text(
                                    text = "✓ Сохранено",
                                    fontSize = 13.sp
                                )
                            }

                            else -> {
                                Text(
                                    text = "↓ Скачать",
                                    fontSize = 13.sp
                                )
                            }
                        }
                    }

                    OutlinedButton(
                        onClick = onDelete,

                        enabled =
                            !deleting &&
                                    !downloading,

                        modifier =
                            Modifier.size(
                                width = 48.dp,
                                height = 48.dp
                            ),

                        contentPadding =
                            PaddingValues(0.dp),

                        shape =
                            RoundedCornerShape(12.dp),

                        colors =
                            ButtonDefaults.outlinedButtonColors(
                                contentColor =
                                    MaterialTheme.colorScheme.error
                            )
                    ) {

                        Text(
                            text = "🗑",
                            fontSize = 17.sp
                        )
                    }
                }

                if (downloading) {

                    LinearProgressIndicator(
                        progress = {
                            downloadProgress / 100f
                        },

                        modifier =
                            Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}

@Composable
fun ReplayThumbnail(
    url: String
) {

    var bitmap by remember(url) {
        mutableStateOf<android.graphics.Bitmap?>(null)
    }

    var loading by remember(url) {
        mutableStateOf(true)
    }

    LaunchedEffect(url) {

        bitmap =
            withContext(Dispatchers.IO) {

                try {

                    val connection =
                        URL(url).openConnection()
                                as HttpURLConnection

                    connection.connectTimeout = 5000
                    connection.readTimeout = 5000
                    connection.requestMethod = "GET"

                    connection.connect()

                    if (
                        connection.responseCode ==
                        HttpURLConnection.HTTP_OK
                    ) {

                        connection.inputStream.use {
                            BitmapFactory.decodeStream(it)
                        }

                    } else {

                        null
                    }

                } catch (_: Exception) {

                    null

                } finally {

                    loading = false
                }
            }
    }

    Box(
        modifier =
            Modifier
                .fillMaxWidth()
                .height(185.dp)
                .background(
                    MaterialTheme.colorScheme.surfaceVariant
                ),

        contentAlignment =
            Alignment.Center
    ) {

        when {

            loading -> {
                CircularProgressIndicator()
            }

            bitmap != null -> {

                AndroidView(

                    factory = { context ->

                        ImageView(context).apply {
                            scaleType =
                                ImageView.ScaleType.CENTER_CROP
                        }
                    },

                    update = { imageView ->
                        imageView.setImageBitmap(bitmap)
                    },

                    modifier =
                        Modifier.fillMaxSize()
                )
            }

            else -> {

                Text(
                    text = "Превью недоступно",

                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
fun EmptyState() {

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp)
    ) {

        Column(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(30.dp),

            horizontalAlignment =
                Alignment.CenterHorizontally
        ) {

            Text(
                text = "○",
                fontSize = 45.sp
            )

            Spacer(
                modifier = Modifier.height(8.dp)
            )

            Text(
                text = "Записей пока нет",

                fontSize = 18.sp,

                fontWeight =
                    FontWeight.Bold
            )

            Spacer(
                modifier = Modifier.height(5.dp)
            )

            Text(
                text =
                    "Сохранённые моменты появятся здесь",

                textAlign =
                    TextAlign.Center,

                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun VideoPlayerScreen(
    replay: ReplayDto,
    onBack: () -> Unit
) {

    val context =
        LocalContext.current

    val videoUrl =
        "http://192.168.0.16:5000/" +
                "api/replays/${replay.id}/video"

    val player =
        remember {

            ExoPlayer.Builder(
                context
            ).build().apply {

                setMediaItem(
                    MediaItem.fromUri(videoUrl)
                )

                prepare()

                playWhenReady = true
            }
        }

    DisposableEffect(player) {

        onDispose {
            player.release()
        }
    }

    Column(
        modifier =
            Modifier
                .fillMaxSize()
                .padding(12.dp),

        verticalArrangement =
            Arrangement.spacedBy(12.dp)
    ) {

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment =
                Alignment.CenterVertically
        ) {

            TextButton(
                onClick = onBack
            ) {

                Text(
                    text = "‹ Назад",
                    fontSize = 18.sp
                )
            }

            Column {

                Text(
                    text = "Replay",
                    fontSize = 19.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text =
                        formatReplayDate(
                            replay.createdAt
                        ),

                    fontSize = 11.sp,

                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Card(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .height(350.dp),

            shape =
                RoundedCornerShape(18.dp)
        ) {

            AndroidView(

                factory = { ctx ->

                    PlayerView(ctx).apply {
                        this.player = player
                        useController = true
                    }
                },

                modifier =
                    Modifier.fillMaxSize()
            )
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp)
        ) {

            Column(
                modifier = Modifier.padding(16.dp),

                verticalArrangement =
                    Arrangement.spacedBy(8.dp)
            ) {

                Text(
                    text =
                        "Replay ${replay.id}",

                    fontSize = 18.sp,

                    fontWeight =
                        FontWeight.Bold
                )

                Text(
                    text =
                        "Длительность: " +
                                formatDuration(
                                    replay.durationSeconds
                                )
                )

                Text(
                    text =
                        "До события: " +
                                "${replay.preSeconds} сек"
                )

                Text(
                    text =
                        "После события: " +
                                "${replay.postSeconds} сек"
                )
            }
        }

        Button(
            onClick = onBack,

            modifier =
                Modifier.fillMaxWidth(),

            shape =
                RoundedCornerShape(14.dp)
        ) {

            Text("← Вернуться к записям")
        }
    }
}

suspend fun downloadReplayToGallery(
    context: android.content.Context,
    replay: ReplayDto,
    onProgress: (Int) -> Unit
): Result<Unit> {

    return withContext(Dispatchers.IO) {

        var connection: HttpURLConnection? = null
        var uri: android.net.Uri? = null

        try {

            val videoUrl =
                "http://192.168.0.16:5000/" +
                        "api/replays/${replay.id}/video"

            connection =
                URL(videoUrl).openConnection()
                        as HttpURLConnection

            connection.connectTimeout = 10000
            connection.readTimeout = 30000
            connection.requestMethod = "GET"

            connection.connect()

            if (
                connection.responseCode !=
                HttpURLConnection.HTTP_OK
            ) {

                throw IOException(
                    "HTTP ${connection.responseCode}"
                )
            }

            val contentLength =
                connection.contentLengthLong

            val date =
                SimpleDateFormat(
                    "yyyy-MM-dd_HH-mm-ss",
                    Locale.getDefault()
                ).format(
                    Date(
                        (replay.createdAt * 1000).toLong()
                    )
                )

            val fileName =
                "replay_$date.mp4"

            val values =
                ContentValues().apply {

                    put(
                        MediaStore.Video.Media.DISPLAY_NAME,
                        fileName
                    )

                    put(
                        MediaStore.Video.Media.MIME_TYPE,
                        "video/mp4"
                    )

                    put(
                        MediaStore.Video.Media.RELATIVE_PATH,
                        "Movies/LifeReplay"
                    )

                    put(
                        MediaStore.Video.Media.IS_PENDING,
                        1
                    )
                }

            val resolver =
                context.contentResolver

            uri =
                resolver.insert(
                    MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
                    values
                )

            if (uri == null) {

                throw IOException(
                    "Не удалось создать файл в галерее"
                )
            }

            try {

                connection.inputStream.use { input ->

                    resolver.openOutputStream(
                        uri
                    ).use { output ->

                        if (output == null) {

                            throw IOException(
                                "Не удалось открыть файл для записи"
                            )
                        }

                        val buffer =
                            ByteArray(8192)

                        var totalBytes = 0L

                        while (true) {

                            val bytesRead =
                                input.read(buffer)

                            if (bytesRead == -1) {
                                break
                            }

                            output.write(
                                buffer,
                                0,
                                bytesRead
                            )

                            totalBytes += bytesRead

                            if (contentLength > 0) {

                                val progress =
                                    (
                                            totalBytes *
                                                    100 /
                                                    contentLength
                                            )
                                        .toInt()
                                        .coerceIn(0, 100)

                                withContext(
                                    Dispatchers.Main
                                ) {
                                    onProgress(progress)
                                }
                            }
                        }

                        output.flush()
                    }
                }

                val completedValues =
                    ContentValues().apply {

                        put(
                            MediaStore.Video.Media.IS_PENDING,
                            0
                        )
                    }

                resolver.update(
                    uri,
                    completedValues,
                    null,
                    null
                )

            } catch (exception: Exception) {

                resolver.delete(
                    uri,
                    null,
                    null
                )

                throw exception
            }

            Result.success(Unit)

        } catch (exception: Exception) {

            exception.printStackTrace()

            Result.failure(exception)

        } finally {

            connection?.disconnect()
        }
    }
}

fun formatFileSize(
    bytes: Long
): String {

    if (bytes < 1024) {
        return "$bytes B"
    }

    if (bytes < 1024 * 1024) {

        return String.format(
            Locale.getDefault(),
            "%.1f KB",
            bytes / 1024.0
        )
    }

    if (bytes < 1024 * 1024 * 1024) {

        return String.format(
            Locale.getDefault(),
            "%.1f MB",
            bytes / (1024.0 * 1024.0)
        )
    }

    return String.format(
        Locale.getDefault(),
        "%.1f GB",
        bytes / (1024.0 * 1024.0 * 1024.0)
    )
}

fun formatDuration(
    seconds: Double
): String {

    val totalSeconds =
        seconds.toInt()

    val minutes =
        totalSeconds / 60

    val remainingSeconds =
        totalSeconds % 60

    return if (minutes > 0) {

        String.format(
            Locale.getDefault(),
            "%d:%02d",
            minutes,
            remainingSeconds
        )

    } else {

        String.format(
            Locale.getDefault(),
            "%.1f сек",
            seconds
        )
    }
}

fun formatReplayDate(
    timestamp: Double
): String {

    return try {

        val date =
            Date(
                (timestamp * 1000).toLong()
            )

        SimpleDateFormat(
            "dd.MM.yyyy • HH:mm:ss",
            Locale.getDefault()
        ).format(date)

    } catch (_: Exception) {

        "Неизвестная дата"
    }
}