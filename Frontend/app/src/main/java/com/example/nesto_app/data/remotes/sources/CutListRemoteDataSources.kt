package com.example.nesto_app.data.remotes.sources

import com.example.nesto_app.data.remotes.services.ProjectService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CutListRemoteDataSources @Inject constructor(
    private val projectService: ProjectService
){
}