package com.example.nesto_app.utils.base

interface Mapper<Response,Model> {
    fun mapFromResponse(type:Response):Model
}