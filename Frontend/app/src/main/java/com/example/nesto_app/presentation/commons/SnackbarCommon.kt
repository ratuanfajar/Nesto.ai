import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarData
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.nesto_app.ui.theme.White
import com.example.nesto_app.utils.ui.CustomSnackbarVisuals
import com.example.nesto_app.utils.ui.SnackbarType

@Composable
fun SnackBarCommon(
    snackbarData: SnackbarData
) {
    val visuals : CustomSnackbarVisuals = snackbarData.visuals as? CustomSnackbarVisuals ?: return
    val type : SnackbarType = visuals.type
    Surface(
        color = type.containerColor,
        modifier = Modifier.padding(top = 40.dp),
        shape = RoundedCornerShape(12.dp),
        tonalElevation = 6.dp
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = visuals.message,
                style = MaterialTheme.typography.titleMedium.copy(
                    color = White,
                ),
                color = type.contentColor
            )
        }
    }
}