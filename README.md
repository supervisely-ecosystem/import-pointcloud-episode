<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/import-pointcloud-episode/releases/download/v1.0.0/poster.png">

# Import Point Cloud Episodes

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>



[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/import-pointcloud-episode)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/import-pointcloud-episode)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/import-pointcloud-episode.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/import-pointcloud-episode.png)](https://supervisely.com)

</div>

## Overview

Import Point Cloud Episodes project in Supervisely format.  
You can learn more about format and its structure by reading [documentation](https://docs.supervisely.com/data-organization/00_ann_format_navi/07_supervisely_format_pointcloud_episode).

Supported point cloud file formats: **`.pcd`**, **`.ply`**, **`.las`**, **`.laz`**.

<video width="100%" src="https://files.gitbook.com/v0/b/gitbook-x-prod.appspot.com/o/spaces%2F9mM1dNm0uHlRsfWgJmow%2Fuploads%2FteQmm0BXOeQlFIgUcpa5%2Fpcde-tool-performance.mp4?alt=media&token=198f6ef1-d93e-40bf-8a1b-f9173adc8a67" autoplay loop muted></video>

Backward compatible with [`Export Supervisely Point Cloud Episodes`](https://ecosystem.supervisely.com/apps/export-pointcloud-episode) app

🏋️ Starting from version `v1.1.3` application supports import from special directory on your local computer. It is made for Enterprise Edition customers who need to upload tens or even hundreds of gigabytes of data without using drag-ang-drop mechanism:

1. Run agent on your computer where data is stored. Watch [how-to video](https://youtu.be/aO7Zc4kTrVg).
2. Copy your data to special folder on your computer that was created by agent. Agent mounts this directory to your Supervisely instance and it becomes accessible in Team Files. Learn more [in documentation](https://docs.supervisely.com/customization/agents/agent-storage). Watch [how-to video](https://youtu.be/63Kc8Xq9H0U).
3. Go to `Team Files` -> `Supervisely Agent` and find your folder there.
4. Right click to open context menu and start app. Now app will upload data directly from your computer to the platform.

# Preparation

Upload your data in Supervisely Point Cloud Episodes [format](https://docs.supervisely.com/data-organization/00_ann_format_navi/07_supervisely_format_pointcloud_episode) to Team Files. It is possible to upload folder or archive (`.tar` or `.zip`).<br>

ℹ️ You can download the archive with data example [here](https://github.com/supervisely-ecosystem/import-pointcloud-episode/files/12546714/my_pointcloud_episodes_project.zip).<br>

Imported project structure has to be the following:
```text
📦 pcd_episodes_project folder or .tar/.zip archive
├── 📜 key_id_map.json (optional)
├── 📜 meta.json
├── 📂 dataset1
│   ├── 📜 annotation.json
│   ├── 📜 frame_pointcloud_map.json
│   ├── 📂 pointcloud
│   │   ├── 📄 scene_1.pcd  (.ply/.las/.laz also supported)
│   │   ├── 📄 scene_2.pcd
│   │   └── ...
│   └── 📂 related_images
│       ├── 📂 scene_1_pcd
│       │   ├── 🖼️ scene_1_cam0.png
│       │   ├── 📜 scene_1_cam0.png.json
│       │   ├── 🖼️ scene_1_cam1.png
│       │   ├── 📜 scene_1_cam1.png.json
│       │   └── ...
│       ├── 📂 scene_2_pcd
│       │   ├── 🖼️ scene_2_cam0.png
│       │   ├── 📜 scene_2_cam0.png.json
│       │   ├── 🖼️ scene_2_cam1.png
│       │   ├── 📜 scene_2_cam1.png.json
│       │   └── ...
│       └── ...
├── 📂 dataset2
│   ├── 📜 annotation.json
│   ├── 📜 frame_pointcloud_map.json
│   ├── 📂 pointcloud
│   │   ├── 📄 scene_1.pcd
│   │   └── ...
│   └── 📂 related_images
│       ├── 📂 scene_1_pcd
│       │   ├── 🖼️ scene_1_cam0.png
│       │   ├── 📜 scene_1_cam0.png.json
│       │   └── ...
│       ├── 📂 scene_2_pcd
│       │   ├── 🖼️ scene_2_cam0.png
│       │   ├── 📜 scene_2_cam0.png.json
│       │   └── ...
│       └── ...
└── 📂 dataset...
```

# How To Run

1. Find the app in **App Ecosystem** and click **Run Application**.
2. Drag & drop your project from the local disk, or choose it from team **Files**.
3. Alternatively, open the context menu on a folder or archive in team **Files** and select `Run app` → `Import` → `Import Point Cloud Episodes`.

<div align="center">
<img src="https://github.com/supervisely-ecosystem/import-pointcloud-episode/releases/download/v1.2.6/ecosystem.jpg" width="90%"/>
</div>

# How To Use 

Wait for the app to import your data (project will be created in the current workspace)

<div align="center">
<img src="https://github.com/supervisely-ecosystem/import-pointcloud-episode/releases/download/v1.2.6/import.jpg" width="90%"/>
</div>
