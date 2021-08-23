/* add polygon centroids as points */
insert into osmpoints (
    select -area_id as node_id, tags, st_centroid(geom) as geom from osmpolygons
);