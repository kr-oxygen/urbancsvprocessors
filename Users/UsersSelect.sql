SELECT
    u.id,
    ct.name as countryname,
    'Prod_' || u.email as email, -- TODO: do not forget to remove 'Prod_' prefix on production migration
    u.created_at,
    u.updated_at,
    u.deleted_at,
    u.stripe_customer_id,
    p.name,
    p.phone_number,
    p.city as personcity,
    a.address,
    a.city as addresscity,
    a.zipcode,
    c.code
FROM
    users as u
        left outer join profiles as p on (u.id = p.user_id)
        left outer join addresses a on (u.address_id = a.id)
        left outer join countries c on (c.id = a.country_id)
        left outer join country_translations ct on  (c.id = ct.country_id)
where u.email !~ '.+@.+_.+'
group by 
    u.id,
    ct.name,
    u.email,
    u.created_at,
    u.updated_at,
    u.deleted_at,
    u.stripe_customer_id,
    p.name,
    p.phone_number,
    p.city,
    a.address,
    a.city,
    a.zipcode,
    c.code
order by u.id
