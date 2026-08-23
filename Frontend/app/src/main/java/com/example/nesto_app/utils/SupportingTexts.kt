package com.example.nesto_app.utils

import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import com.example.nesto_app.ui.theme.error
import com.example.nesto_app.utils.base.BaseSupportingText

object NormalSupportingText : BaseSupportingText {
    @Composable
    override fun SupportText(text: String, style: TextStyle) {
        if (text.isBlank())
            Text("Cannot be blank",style = style)
    }

    @Composable
    fun SupportText(
        text: String,
        title: String,
        style: TextStyle = Typography.error
    ) {
        if (text.isBlank())
            Text("$title Cannot be blank",style = style)
    }

    override fun validate(text: String): Boolean {
        return text.isNotBlank()
    }
}

object NumberSupportingText : BaseSupportingText {
    @Composable
    override fun SupportText(text: String, style: TextStyle) {
        if (text.isBlank())
            Text("Cannot be blank",style = style)
        if (text.toInt() < 0)
            Text("Cannot be lower than 0",style = style)
    }

    override fun validate(text: String): Boolean {
        return text.isNotBlank() && text.toInt() > 0
    }
}