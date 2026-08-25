package com.example.nesto_app.data.repositories

import android.content.Context
import android.net.Uri
import android.util.Log
import com.example.nesto_app.data.remotes.sources.CutListRemoteDataSources
import com.example.nesto_app.domain.entities.CutList
import com.example.nesto_app.domain.repositories.CutListRepository
import com.example.nesto_app.mapper.CutListMapper
import com.example.nesto_app.utils.State
import com.example.nesto_app.utils.exceptions.getErrorMessage
import com.example.nesto_app.utils.toMultipart
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject

class CutListRepositoryImpl @Inject constructor(
    private val cutListRemoteDataSources: CutListRemoteDataSources,
    @ApplicationContext
    private val context: Context,
): CutListRepository {
    override suspend fun analyze(images : List<Uri>): Flow<State<CutList>> = flow {
        emit(State.Loading())
        try {
            val imagesMultipart = images.map {
                it.toMultipart(context,"image")
            }
            val response = cutListRemoteDataSources.analyze(imagesMultipart)
            val cutList = CutListMapper().mapFromResponse(response)
            emit(State.Success<CutList>(data = cutList))
        } catch (e: retrofit2.HttpException) {
            val message = e.getErrorMessage()
            emit(State.Error(message = message))
        } catch (e: Exception) {
            Log.d("Error Exception Repo",e.message.toString())
            emit(State.Error(message = e.message.toString()))
        }
    }
}