import kotlinx.serialization.Serializable

object WorkerRoutes {
    @Serializable
    object Home

//    CutList
    @Serializable
    object CreateCutList
    @Serializable
    object UpdateCutList
    @Serializable
    data class DetailCutList(val cutListId: Int)

//    Project
    @Serializable
    object CreateProject
    @Serializable
    object UpdateProject
    @Serializable
    data class DetailProject(val projectId: Int)
}