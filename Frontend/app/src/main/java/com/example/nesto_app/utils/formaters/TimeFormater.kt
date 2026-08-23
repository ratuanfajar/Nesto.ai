package com.example.nesto_app.utils.formaters

import android.os.Build
import androidx.annotation.RequiresApi
import kotlinx.datetime.TimeZone
import kotlinx.datetime.number
import kotlinx.datetime.toJavaLocalDateTime
import kotlinx.datetime.toLocalDateTime
import java.time.format.DateTimeFormatter
import kotlin.time.ExperimentalTime
import kotlin.time.Instant

object TimeFormater {
    @OptIn(ExperimentalTime::class)
    fun Instant.toDisplayString(): String {
        val dateTime = toLocalDateTime(TimeZone.currentSystemDefault())

        val month = when (dateTime.month.number) {
            1 -> "Jan"
            2 -> "Feb"
            3 -> "Mar"
            4 -> "Apr"
            5 -> "May"
            6 -> "Jun"
            7 -> "Jul"
            8 -> "Aug"
            9 -> "Sep"
            10 -> "Oct"
            11 -> "Nov"
            12 -> "Dec"
            else -> ""
        }

        return "%02d %s %04d %02d:%02d".format(
            dateTime.day,
            month,
            dateTime.year,
            dateTime.hour,
            dateTime.minute
        )
    }
}