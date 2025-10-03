create
or replace view usage_report_v as
select user_id, project_id, year, month, day, resource_type, sum (unit_count) as tokens
from usage_v
group by user_id, project_id, year, month, day, resource_type
order by year desc, month desc, day desc, resource_type;

select *
from usage_report_v
where user_id = 'dc688d73-af47-b1df-a24e-b7dfdb618b54'
          and year is not null;

drop view usage_report_aggregate_v;
create
or replace view usage_report_aggregate_v as
select date_trunc('day', transaction_time) as daily,
       project_id,
       resource_type                       as provider,
       unit_type,
       unit_subtype,
       count(id)                           as call_count,
       sum(unit_count)                     as sum_units,
       trunc(avg(unit_count), 2)           as avg_units,
       min(unit_count)                     as min_units,
       max(unit_count)                     as max_units
from usage
--where project_id = '4cfa8c17-420e-4812-aa6b-544bb3ae49f9'
group by daily, project_id, resource_type, unit_type, unit_subtype
order by daily desc;


create
or replace view usage_report_aggregate_pricing_v as
WITH pricing AS (
    select u.*,
           CASE
               WHEN unit_subtype = 'OUTPUT' THEN p.output_price_per_1k_tokens
               WHEN unit_subtype = 'INPUT' THEN p.input_price_per_1k_tokens
               ELSE NULL
           END AS price_per_unit
      from usage_report_aggregate_v u
     left outer join processor_provider_pricing p
      on u.provider = p.processor_provider_id
)
select *, price_per_unit * sum_units / 1000 as cost
from pricing;


select *
from usage_report_aggregate_pricing_v
where project_id = '4cfa8c17-420e-4812-aa6b-544bb3ae49f9'
  and daily = '2025-10-02';