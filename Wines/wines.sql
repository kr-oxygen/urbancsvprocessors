select
    distinct w.id as wineid,
    w.name winename,
    p.id as producerid,
    p.name as producername,
    case
        when ct.name = 'USA' then 'United States'
        when ct.name = 'England' then 'United Kingdom'
        when ct.name = 'Macedonia, Republic of' then 'Macedonia'
        else ct.name
    end as winecountry,
    case 
        when ct.name = 'Luxembourg' and w.district_id is null then ct.name
        when ct.name = 'Macedonia' and w.district_id is null then ct.name
        when ct.name = 'Morocco' and w.district_id is null then ct.name
        when ct.name = 'Norway' and w.district_id is null then ct.name
        when ct.name = 'Peru' and w.district_id is null then ct.name
        when ct.name = 'Romania' and w.district_id is null then ct.name
        when ct.name = 'Slovakia' and w.district_id is null then ct.name
        when ct.name = 'Czech Republic' and w.district_id is null then ct.name
        when ct.name = 'Denmark' and w.district_id is null then ct.name
        when ct.name = 'Sweden' and w.district_id is null then ct.name
        when ct.name = 'Thailand' and w.district_id is null then ct.name
        when ct.name = 'Turkey' and w.district_id is null then ct.name
        when ct.name = 'Albania' and w.district_id is null then ct.name
        when ct.name = 'Belgium' and w.district_id is null then ct.name
        when ct.name = 'Brazil' and w.district_id is null then ct.name
        when ct.name = 'Bulgaria' and w.district_id is null then ct.name
        when ct.name = 'Uruguay' and w.district_id is null then ct.name
        when ct.name = 'Japan' and w.district_id is null then ct.name
        else substring(dt.name from '.+ - (.+)')
    end as wineregion,
    w.appellation,
    case 
        when wt.name = 'Rødvin' then 'Red wine'
        when wt.name = 'Sød vin' then 'Sweet wine'
        when wt.name = 'Cider' then 'Cider'
        when wt.name = 'Portvin' then 'Port'
        when wt.name = 'Frugtvin' then 'Fruit wines'
        when wt.name = 'Mousserende vin' then 'Sparkling wine'
        when wt.name = 'Hvidvin' then 'White wine'
        when wt.name = 'Rosé' then 'Rose'
        else 'Others'
    end as winetype,
    case
        when pct.name = 'USA' then 'United States'
        when pct.name = 'England' then 'United Kingdom'
        when pct.name = 'Macedonia, Republic of' then 'Macedonia'
        else pct.name
    end 
     as producercountry,
    substring(pdt.name from '.+ - (.+)') as producerdistrict
from
    wines as w
        left join producers as p on p.id = w.producer_id
        left join wine_type_translations as wt on w.wine_type_id = wt.wine_type_id
        left join country_translations as ct on ct.country_id = w.country_id
        left join district_translations as dt on dt.district_id = w.district_id
        left join country_translations as pct on p.country_id = pct.country_id
        left join district_translations as pdt on p.district_id = pdt.district_id

    
