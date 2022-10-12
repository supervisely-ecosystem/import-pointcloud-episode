<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/import-pointcloud-episode/releases/download/v1.0.0/poster.png">

# Import Pointcloud Episodes

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>



[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/import-pointcloud-episode)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/import-pointcloud-episode)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/import-pointcloud-episode.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/import-pointcloud-episode.png)](https://supervise.ly)

</div>

## Overview

Import Supervisely pointcloud episodes format project from Team Files folder or archive.  
You can learn more about format and its structure by reading [documentation](https://docs.supervise.ly/data-organization/00_ann_format_navi/07_supervisely_format_pointcloud_episode).

<img src="https://github.com/supervisely-ecosystem/import-kitti-360/releases/download/v0.0.4/pointcloud-episodes.gif?raw=true" style="width: 100%;"/>

Backward compatible with [`Export Supervisely Pointcloud Episodes`](https://ecosystem.supervise.ly/apps/export-pointcloud-episode) app

🏋️ Starting from version `v1.1.0` application supports import from special directory on your local computer. It is made for Enterprise Edition customers who need to upload tens or even hundreds of gigabytes of data without using drag-ang-drop mechanism:

1. Run agent on your computer where data is stored.
2. Copy your data to special folder on your computer that was created by agent. Agent mounts this directory to your Supervisely instance and it becomes accessible in Team Files. Learn more [in documentation](https://github.com/supervisely/docs/blob/master/customization/agents/agent-storage/agent-storage.md).
3. Go to `Team Files` -> `Supervisely Agent` and find your folder there.
4. Right click to open context menu and start app. Now app will upload data directly from your computer to the platform.

# Preparation

Upload your data in Supervisely pointcloud episodes [format](https://docs.supervise.ly/data-organization/00_ann_format_navi/07_supervisely_format_pointcloud_episode) to Team Files. It is possible to upload folder or archive (`.tar` or `.zip`).

Imported project structure has to be the following:
```text
pcd_episodes_project folder or .tar/.zip archive   
├── key_id_map.json (optional)                
├── meta.json     
├── dataset1                        
│ ├── annotation.json               
│ ├── frame_pointcloud_map.json     
│ ├── pointcloud                    
│ │ ├── scene_1.pcd           
│ │ ├── scene_2.pcd   
│ │ └── ...                
│ └── related_images                
│     ├── scene_1_pcd               
│     │ ├── scene_1_cam0.png       
│     │ ├── scene_1_cam0.png.json  
│     │ ├── scene_1_cam1.png       
│     │ ├── scene_1_cam1.png.json  
│     │ └── ... 
│     ├── scene_2_pcd               
│     │ ├── scene_2_cam0.png       
│     │ ├── scene_2_cam0.png.json  
│     │ ├── scene_2_cam1.png       
│     │ ├── scene_2_cam1.png.json  
│     │ └── ... 
│     └── ...      
├── dataset2                        
│ ├── annotation.json               
│ ├── frame_pointcloud_map.json     
│ ├── pointcloud                    
│ │ ├── scene_1.pcd                 
│ │ └── ...               
│ └── related_images                
│     ├── scene_1_pcd               
│     │ ├── scene_1_cam0.png       
│     │ ├── scene_1_cam0.png.json    
│     │ └── ... 
│     ├── scene_2_pcd               
│     │ ├── scene_2_cam0.png       
│     │ ├── scene_2_cam0.png.json  
│     │ └── ... 
│     └── ...                    
└── dataset...                       
```

# How To Run 

1. Add [Import Supervisely pointcloud episodes](https://ecosystem.supervise.ly/apps/import-pointcloud-episode) to your team from Ecosystem.

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/import-pointcloud-episode" src="https://i.imgur.com/JRM9WXO.png" width="450px" style='padding-bottom: 20px'/>  

2. Run app from the context menu of directory or archive in **Team Files** -> `Run app` -> `Import pointcloud episodes in supervisely format`

<img src="https://i.imgur.com/AOhFNgm.png"/>

# How To Use 

1. Wait for the app to import your data (project will be created in the current workspace)

<img src="https://i.imgur.com/UjcZZgP.png"/>  
