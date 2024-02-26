from collections import defaultdict
from typing import Optional
import click
from .ip import get_ipv4, get_ipv6
from .glesys import GleSYS, GleSYSError, Record


@click.command
@click.argument("hosts", type=str, nargs=-1)
@click.option("--api-user", type=str,
    help="User ID the GleSYS user ID to operate as. Read from environment variable GLESYS_API_USER if not specified."
)
@click.option("--api-key", type=str,
    help="GleSYS API key for authorization. Read from environment variable GLESYS_API_KEY if not specified."
)
def update_records(
    hosts: list[str],
    api_user: str,
    api_key: str,
) -> None:
    try:
        glesys = GleSYS(api_user, api_key)
        domains = get_domains(hosts)

        invalid_subdomains = {d for d, sd in domains.items() if not sd}
        if invalid_subdomains:
            raise click.UsageError(f"the following hostnames contain no subdomain: {', '.join(invalid_subdomains)}")

        records = {d: glesys.list_records(d) for d in domains.keys()}
        
        missing_records = get_missing_records(records, domains)
        if missing_records:
            raise click.UsageError(f"the following DNS records do not exist: {', '.join(missing_records)}")

        ipv4 = get_ipv4()
        ipv6 = get_ipv6()
        for domain, records_to_update in domains.items():
            update_domain_records(glesys, ipv4, ipv6, records[domain], records_to_update)
    except GleSYSError as e:
        raise click.UsageError(e.message())


def update_domain_records(
    glesys: GleSYS,
    ipv4: Optional[str],
    ipv6: Optional[str],
    domain_records: list[Record],
    records_to_update: set[str]
) -> None:
    for record in (r for r in domain_records if r.host in records_to_update):
        if record.type == "A" and ipv4:
            record.data = ipv4
        if record.type == "AAAA" and ipv6:
            record.data = ipv6
        glesys.update_record(record)


def get_missing_records(
    records: dict[str, list[Record]],
    domains: dict[str, set[str]]
) -> set[str]:
    missing_records = set[str]()
    for domain, subdomains in domains.items():
        existing_hosts = {r.host for r in records[domain]}
        missing_records.update({f"{sd}.{domain}" for sd in subdomains - existing_hosts})
    return missing_records


def split_host(host: str) -> tuple[str, Optional[str]]:
    """Split a hostname into domain and subdomain parts."""
    parts = host.split(".")
    domain = ".".join(parts[-2:])
    subdomain = ".".join(parts[:-2])
    return (domain, subdomain or None)


def get_domains(hosts: list[str]) -> dict[str, set[str]]:
    "Break a list of hostnames into a dictionary from domains to the set of all subdomains for that domain."
    domains = defaultdict[str, set[str]](set)
    for host in hosts:
        domain, subdomain = split_host(host)
        if subdomain:
            domains[domain].add(subdomain)
        else:
            # Don't silently ignore invalid subdomains
            domains[domain] = set()
    return domains


if __name__ == "__main__":
    update_records(auto_envvar_prefix="GLESYS")
