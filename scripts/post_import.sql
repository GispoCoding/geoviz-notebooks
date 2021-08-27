/* add primary key to prevent duplicate imports */
alter table osmpoints add primary key (node_id);

/* add polygon centroids as points */
/* only add points not existing yet */
insert into osmpoints (
    select -area_id as node_id, tags, st_centroid(geom) as geom from osmpolygons
) on conflict (node_id) do nothing;