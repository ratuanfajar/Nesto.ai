package com.example.nesto_app.data.repositories

import com.example.nesto_app.data.remotes.sources.ProjectRemoteDataSources
import com.example.nesto_app.domain.repositories.ProjectRepository
import javax.inject.Inject

class ProjectRepositoryImpl @Inject constructor(
    private val projectRemoteDataSources: ProjectRemoteDataSources
): ProjectRepository {

}