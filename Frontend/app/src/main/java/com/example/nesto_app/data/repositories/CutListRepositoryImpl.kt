package com.example.nesto_app.data.repositories

import com.example.nesto_app.data.remotes.sources.CutListRemoteDataSources
import com.example.nesto_app.domain.repositories.CutListRepository
import javax.inject.Inject

class CutListRepositoryImpl @Inject constructor(
    private val cutListRemoteDataSources: CutListRemoteDataSources
): CutListRepository {

}