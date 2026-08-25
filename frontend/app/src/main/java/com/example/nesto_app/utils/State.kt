package com.example.nesto_app.utils

sealed class State<T> {
    class Loading<T> : State<T>()
    data class Success<T>(val data: T) : State<T>()
    data class Error<T>(val message: String, val data:T? = null) : State<T>()
}