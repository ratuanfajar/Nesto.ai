package com.example.nesto_app.utils.base

import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import com.example.nesto_app.ui.theme.error

interface BaseSupportingText {
    @Composable fun SupportText(text: String,style: TextStyle = Typography.error)
    fun validate(text:String) : Boolean

}