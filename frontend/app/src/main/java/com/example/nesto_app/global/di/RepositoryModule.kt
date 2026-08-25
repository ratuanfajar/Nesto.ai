package com.example.nesto_app.global.di

import com.example.nesto_app.data.repositories.CutListRepositoryImpl
import com.example.nesto_app.data.repositories.ProjectRepositoryImpl
import com.example.nesto_app.domain.repositories.CutListRepository
import com.example.nesto_app.domain.repositories.ProjectRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindProjectRepository(
        impl: ProjectRepositoryImpl
    ): ProjectRepository

    @Binds
    @Singleton
    abstract fun bindCutListRepository(
        impl: CutListRepositoryImpl
    ): CutListRepository
}