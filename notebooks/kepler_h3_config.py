config = {
    "version": "v1",
    "config": {
      "visState": {
        "filters": [],
        "layers": [
          {
            "id": "5tldd4g",
            "type": "geojson",
            "config": {
              "dataId": "data_1",
              "label": "data_1",
              "color": [
                241,
                92,
                23
              ],
              "columns": {
                "geojson": "geometry"
              },
              "isVisible": False,
              "visConfig": {
                "opacity": 0.8,
                "strokeOpacity": 0.8,
                "thickness": 0.5,
                "strokeColor": None,
                "colorRange": {
                  "name": "Global Warming",
                  "type": "sequential",
                  "category": "Uber",
                  "colors": [
                    "#5A1846",
                    "#900C3F",
                    "#C70039",
                    "#E3611C",
                    "#F1920E",
                    "#FFC300"
                  ]
                },
                "strokeColorRange": {
                  "name": "Global Warming",
                  "type": "sequential",
                  "category": "Uber",
                  "colors": [
                    "#5A1846",
                    "#900C3F",
                    "#C70039",
                    "#E3611C",
                    "#F1920E",
                    "#FFC300"
                  ]
                },
                "radius": 10,
                "sizeRange": [
                  0,
                  10
                ],
                "radiusRange": [
                  0,
                  50
                ],
                "heightRange": [
                  0,
                  500
                ],
                "elevationScale": 5,
                "stroked": False,
                "filled": True,
                "enable3d": False,
                "wireframe": False
              },
              "hidden": False,
              "textLabel": [
                {
                  "field": None,
                  "color": [
                    255,
                    255,
                    255
                  ],
                  "size": 18,
                  "offset": [
                    0,
                    0
                  ],
                  "anchor": "start",
                  "alignment": "center"
                }
              ]
            },
            "visualChannels": {
              "colorField": None,
              "colorScale": "quantile",
              "sizeField": None,
              "sizeScale": "linear",
              "strokeColorField": None,
              "strokeColorScale": "quantile",
              "heightField": None,
              "heightScale": "linear",
              "radiusField": None,
              "radiusScale": "linear"
            }
          },
          {
            "id": "k21aij8",
            "type": "hexagonId",
            "config": {
              "dataId": "data_1",
              "label": "hex7",
              "color": [
                34,
                63,
                154
              ],
              "columns": {
                "hex_id": "hex7"
              },
              "isVisible": True,
              "visConfig": {
                "opacity": 0.8,
                "colorRange": {
                  "name": "Global Warming",
                  "type": "sequential",
                  "category": "Uber",
                  "colors": [
                    "#5A1846",
                    "#900C3F",
                    "#C70039",
                    "#E3611C",
                    "#F1920E",
                    "#FFC300"
                  ]
                },
                "coverage": 1,
                "enable3d": False,
                "sizeRange": [
                  0,
                  500
                ],
                "coverageRange": [
                  0,
                  1
                ],
                "elevationScale": 5
              },
              "hidden": False,
              "textLabel": [
                {
                  "field": None,
                  "color": [
                    255,
                    255,
                    255
                  ],
                  "size": 18,
                  "offset": [
                    0,
                    0
                  ],
                  "anchor": "start",
                  "alignment": "center"
                }
              ]
            },
            "visualChannels": {
              "colorField": {
                "name": "size",
                "type": "integer"
              },
              "colorScale": "quantize",
              "sizeField": None,
              "sizeScale": "linear",
              "coverageField": None,
              "coverageScale": "linear"
            }
          }
        ],
        "interactionConfig": {
          "tooltip": {
            "fieldsToShow": {
              "data_1": [
                {
                  "name": "size",
                  "format": None
                },
                {
                  "name": "hex8",
                  "format": None
                }
              ]
            },
            "compareMode": False,
            "compareType": "absolute",
            "enabled": True
          },
          "brush": {
            "size": 0.5,
            "enabled": False
          },
          "geocoder": {
            "enabled": False
          },
          "coordinate": {
            "enabled": False
          }
        },
        "layerBlending": "normal",
        "splitMaps": [],
        "animationConfig": {
          "currentTime": None,
          "speed": 1
        }
      },
      "mapState": {
        "bearing": 0,
        "dragRotate": False,
        "latitude": 60.14247930383862,
        "longitude": 23.784654539638225,
        "pitch": 0,
        "zoom": 6.382620658788189,
        "isSplit": False
      },
      "mapStyle": {
        "styleType": "dark",
        "topLayerGroups": {},
        "visibleLayerGroups": {
          "label": True,
          "road": True,
          "border": False,
          "building": True,
          "water": True,
          "land": True,
          "3d building": False
        },
        "threeDBuildingColor": [
          9.665468314072013,
          17.18305478057247,
          31.1442867897876
        ],
        "mapStyles": {}
      }
    }
  }
