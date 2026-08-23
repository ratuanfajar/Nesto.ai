package com.example.nesto_app.global.navigations.worker

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.toRoute
import com.example.nesto_app.presentation.worker.home.HomeWorkerScreen


@Composable
fun WorkerNavHost(
    workerNavController: NavHostController,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = workerNavController,
        startDestination = WorkerRoutes.Home,
        modifier = modifier
    ) {
        composable<WorkerRoutes.Home> {
            HomeWorkerScreen(
                navController = workerNavController
            )
        }
    }
}