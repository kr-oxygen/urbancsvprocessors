select
    distinct p.id,
    p.name as producer, 
    case 
        when ct.name = 'USA' then 'United States'
        when ct.name = 'England' then 'United Kingdom'
        when ct.name = 'Macedonia, Republic of' then 'Macedonia'
        else ct.name
    end as country,
    substring(dt.name from '.+ - (.+)') as district
from 
producers as p
    left outer join country_translations as ct on p.country_id = ct.country_id
    left outer join district_translations as dt on p.district_id = dt.district_id
order by p.name
--group by p.id, p.name, dt.name, ct.name
    
--select count(id) from producers