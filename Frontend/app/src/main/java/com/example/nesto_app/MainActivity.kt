package com.example.nesto_app

import SnackBarCommon
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.rememberNavController
import com.example.nesto_app.global.navigations.RootNavGraph
import com.example.nesto_app.ui.theme.Nesto_AppTheme
import com.example.nesto_app.utils.ui.AppEventBus
import com.example.nesto_app.utils.ui.UiEvent
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            Nesto_AppTheme {
                AppRoot()
            }
        }
    }
}

@Composable
fun AppRoot(
) {
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val navController = rememberNavController()
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        LaunchedEffect(Unit) {
            AppEventBus.events.collect { event ->
                when(event){
                    is UiEvent.ShowSnackbar ->{
                        scope.launch {
                            snackbarHostState.currentSnackbarData?.dismiss()
                            snackbarHostState.showSnackbar(event.data)
                        }
                    }
                }
            }
        }
        RootNavGraph(navController)
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .fillMaxSize()
                .wrapContentSize(Alignment.TopCenter),
            snackbar = {
                    data -> Box(
                modifier = Modifier.padding(horizontal = 16.dp)
            ) {
                SnackBarCommon(data)
            }
        })
    }
}