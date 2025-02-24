#!/usr/bin/env python3
# Copyright (C) 2020 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# We use the ordering of graphs from Checkmk 2.2 because the graphing API came with Checkmk 2.3
GRAPHS_2_2 = [
    "apache_status",
    "bufferpool_hitratios",
    "deadlocks_and_waits",
    "licenses",
    "current_users",
    "firewall_users",
    "mobileiron_compliances",
    "messages",
    "cpu_credits",
    "aws_ec2_running_ondemand_instances",
    "aws_http_nxx_errors_rate",
    "aws_http_50x_errors_rate",
    "aws_http_nxx_errors_perc",
    "aws_http_50x_errors_perc",
    "aws_dynamodb_read_capacity_single",
    "aws_dynamodb_write_capacity_single",
    "aws_dynamodb_query_latency",
    "aws_dynamodb_getitem_latency",
    "aws_dynamodb_putitem_latency",
    "aws_wafv2_web_acl_requests",
    "aws_cloudfront_errors_rate",
    "bucket_size",
    "num_objects",
    "buckets",
    "livestatus_requests_per_connection",
    "livestatus_usage",
    "helper_usage_cmk",
    "helper_usage_fetcher",
    "helper_usage_checker",
    "helper_usage_generic",
    "average_check_latency",
    "average_fetcher_latency",
    "pending_updates",
    "handled_requests",
    "cmk_http_pagetimes",
    "cmk_http_traffic",
    "host_and_service_checks",
    "number_of_monitored_hosts_and_services",
    "livestatus_connects_and_requests",
    "message_processing",
    "rule_efficiency",
    "inbound_and_outbound_messages",
    "cmk_hosts_total",
    "cmk_hosts_not_up",
    "cmk_services_total",
    "cmk_services_not_ok",
    "citrix_serverload",
    "couchbase_bucket_memory",
    "couchbase_bucket_fragmentation",
    "used_cpu_time",
    "cmk_cpu_time_by_phase",
    "cpu_time",
    "tapes_utilization",
    "storage_processor_utilization",
    "cpu_load",
    "fgpa_utilization",
    "util_average_1",
    "util_average_2",
    "cpu_utilization_numcpus",
    "cpu_utilization_simple",
    "cpu_utilization_3",
    "cpu_utilization_4",
    "cpu_utilization_5",
    "cpu_utilization_5_util",
    "cpu_utilization_6_steal",
    "cpu_utilization_6_steal_util",
    "cpu_utilization_6_guest",
    "cpu_utilization_6_guest_util",
    "cpu_utilization_7",
    "cpu_utilization_7_util",
    "cpu_utilization_8",
    "cpu_utilization_percentile",
    "util_fallback",
    "cpu_entitlement",
    "per_core_utilization",
    "per_core_utilization_average",
    "context_switches",
    "threads",
    "thread_usage",
    "threadpool",
    "memory_utilization_percentile",
    "cpu_utilization",
    "docker_containers",
    "docker_df",
    "docker_df_count",
    "shards_allocation",
    "active_shards",
    "emcvnx_storage_pools_capacity",
    "emcvnx_storage_pools_movement",
    "emcvnx_storage_pools_targeted",
    "fan_speed",
    "battery_currents",
    "battery_capacity",
    "optical_signal_power",
    "optical_signal_power_lane_0",
    "optical_signal_power_lane_1",
    "optical_signal_power_lane_2",
    "optical_signal_power_lane_3",
    "optical_signal_power_lane_4",
    "optical_signal_power_lane_5",
    "optical_signal_power_lane_6",
    "optical_signal_power_lane_7",
    "optical_signal_power_lane_8",
    "optical_signal_power_lane_9",
    "temperature",
    "fc_errors",
    "fc_errors_detailed",
    "throughput",
    "frames",
    "words",
    "fs_used",
    "fs_used_2",
    "growing",
    "shrinking",
    "fs_trend",
    "faas_execution_times",
    "faas_execution_times_2xx",
    "faas_execution_times_3xx",
    "faas_execution_times_4xx",
    "faas_execution_times_5xx",
    "faas_memory_size_absolute",
    "bar1_mem_usage",
    "fb_mem_usage",
    "ibm_mq_queue_procs",
    "ibm_mq_qtime",
    "number_of_executors",
    "number_of_tasks",
    "kube_pod_resources",
    "kube_resources_terminated",
    "kube_node_container_count",
    "kube_memory_usage",
    "kube_cpu_usage",
    "kube_node_count_worker",
    "kube_node_count_control_plane",
    "kube_pod_restarts",
    "kube_replica_available_state",
    "kube_replica_state",
    "kube_replica_update_state",
    "kube_cronjob_status",
    "k8s_resources.pods",
    "k8s_resources.pod",
    "k8s_resources.cpu",
    "k8s_resources.memory",
    "k8s_pod_container",
    "amount_of_mails_in_queues",
    "size_of_mails_in_queues",
    "amount_of_mails_in_secondary_queues",
    "mqtt_clients",
    "bytes_transmitted",
    "messages_transmitted",
    "publish_bytes_transmitted",
    "publish_messages_transmitted",
    "read_write_data",
    "savings",
    "nfs_traffic",
    "nfs_latency",
    "nfs_ops",
    "cifs_traffic",
    "cifs_latency",
    "cifs_ops",
    "san_traffic",
    "san_latency",
    "san_ops",
    "fcp_traffic",
    "fcp_latency",
    "fcp_ops",
    "iscsi_traffic",
    "iscsi_latency",
    "iscsi_ops",
    "nfsv4_traffic",
    "nfsv4_latency",
    "nfsv4_ops",
    "nfsv4_1_traffic",
    "nfsv4_1_latency",
    "nfsv4_1_ops",
    "bandwidth_translated",
    "bandwidth",
    "if_errors_discards",
    "bm_packets",
    "packets_1",
    "packets_2",
    "packets_3",
    "traffic",
    "wlan_errors",
    "busy_and_idle_workers",
    "busy_and_idle_servers",
    "total_and_open_slots",
    "connections",
    "time_offset",
    "last_sync_time",
    "firewall_connections",
    "time_to_connect",
    "number_of_total_and_running_sessions",
    "tcp_connection_states",
    "db_connections",
    "cluster_hosts",
    "modems",
    "net_data_traffic",
    "access_point_statistics",
    "access_point_statistics2",
    "wifi_connections",
    "round_trip_average",
    "packet_loss",
    "hop_1_round_trip_average",
    "hop_1_packet_loss",
    "hop_2_round_trip_average",
    "hop_2_packet_loss",
    "hop_3_round_trip_average",
    "hop_3_packet_loss",
    "hop_4_round_trip_average",
    "hop_4_packet_loss",
    "hop_5_round_trip_average",
    "hop_5_packet_loss",
    "hop_6_round_trip_average",
    "hop_6_packet_loss",
    "hop_7_round_trip_average",
    "hop_7_packet_loss",
    "hop_8_round_trip_average",
    "hop_8_packet_loss",
    "hop_9_round_trip_average",
    "hop_9_packet_loss",
    "hop_10_round_trip_average",
    "hop_10_packet_loss",
    "hop_11_round_trip_average",
    "hop_11_packet_loss",
    "hop_12_round_trip_average",
    "hop_12_packet_loss",
    "hop_13_round_trip_average",
    "hop_13_packet_loss",
    "hop_14_round_trip_average",
    "hop_14_packet_loss",
    "hop_15_round_trip_average",
    "hop_15_packet_loss",
    "hop_16_round_trip_average",
    "hop_16_packet_loss",
    "hop_17_round_trip_average",
    "hop_17_packet_loss",
    "hop_18_round_trip_average",
    "hop_18_packet_loss",
    "hop_19_round_trip_average",
    "hop_19_packet_loss",
    "hop_20_round_trip_average",
    "hop_20_packet_loss",
    "hop_21_round_trip_average",
    "hop_21_packet_loss",
    "hop_22_round_trip_average",
    "hop_22_packet_loss",
    "hop_23_round_trip_average",
    "hop_23_packet_loss",
    "hop_24_round_trip_average",
    "hop_24_packet_loss",
    "hop_25_round_trip_average",
    "hop_25_packet_loss",
    "hop_26_round_trip_average",
    "hop_26_packet_loss",
    "hop_27_round_trip_average",
    "hop_27_packet_loss",
    "hop_28_round_trip_average",
    "hop_28_packet_loss",
    "hop_29_round_trip_average",
    "hop_29_packet_loss",
    "hop_30_round_trip_average",
    "hop_30_packet_loss",
    "hop_31_round_trip_average",
    "hop_31_packet_loss",
    "hop_32_round_trip_average",
    "hop_32_packet_loss",
    "hop_33_round_trip_average",
    "hop_33_packet_loss",
    "hop_34_round_trip_average",
    "hop_34_packet_loss",
    "hop_35_round_trip_average",
    "hop_35_packet_loss",
    "hop_36_round_trip_average",
    "hop_36_packet_loss",
    "hop_37_round_trip_average",
    "hop_37_packet_loss",
    "hop_38_round_trip_average",
    "hop_38_packet_loss",
    "hop_39_round_trip_average",
    "hop_39_packet_loss",
    "hop_40_round_trip_average",
    "hop_40_packet_loss",
    "hop_41_round_trip_average",
    "hop_41_packet_loss",
    "hop_42_round_trip_average",
    "hop_42_packet_loss",
    "hop_43_round_trip_average",
    "hop_43_packet_loss",
    "hop_44_round_trip_average",
    "hop_44_packet_loss",
    "hop_response_time",
    "palo_alto_sessions",
    "page_activity",
    "authentication_failures",
    "allocate_requests_exceeding_port_limit",
    "packets_dropped",
    "streams",
    "dhcp_statistics_received",
    "dhcp_statistics_sent",
    "dns_statistics",
    "connection_durations",
    "http_timings",
    "web_gateway_statistics",
    "web_gateway_miscellaneous_statistics",
    "DB_connections",
    "http_errors",
    "inodes_used",
    "nodes_by_type",
    "channel_utilization_24ghz",
    "channel_utilization_5ghz",
    "active_sessions_with_peak_value",
    "data_transfer",
    "latencies",
    "connection_count",
    "requests",
    "transactions",
    "server_latency",
    "e2e_latency",
    "availability",
    "read_latency",
    "write_latency",
    "omd_fileusage",
    "oracle_physical_io",
    "oracle_hit_ratio",
    "oracle_db_time_statistics",
    "oracle_buffer_pool_statistics",
    "oracle_library_cache_statistics",
    "oracle_sga_pga_total",
    "oracle_sga_info",
    "oracle_iostat_bytes",
    "oracle_iostat_total_bytes",
    "oracle_iostat_ios",
    "oracle_iostat_total_ios",
    "oracle_wait_class",
    "oracle_pga_memory_info",
    "printer_queue",
    "supply_toner_cyan",
    "supply_toner_magenta",
    "supply_toner_yellow",
    "supply_toner_black",
    "supply_toner_other",
    "printed_pages",
    "number_of_processes",
    "size_of_processes",
    "size_per_process",
    "qos_class_traffic",
    "rmon_packets_per_second",
    "active_sessions",
    "read_and_written_blocks",
    "disk_rw_latency",
    "disk_latency",
    "read_write_queue_length",
    "backup_time",
    "total_cache_usage",
    "write_cache_usage",
    "zfs_meta_data",
    "cache_hit_ratio",
    "wasted_space_of_tables_and_indexes",
    "disk_utilization",
    "disk_throughput",
    "disk_io_operations",
    "direct_and_buffered_io_operations",
    "average_request_size",
    "average_end_to_end_wait_time",
    "spare_and_broken_disks",
    "database_sizes",
    "number_of_shared_and_exclusive_locks",
    "tablespace_sizes",
    "ram_swap_used",
    "mem_used_percent",
    "cpu_mem_used_percent",
    "mem_trend",
    "mem_growing",
    "mem_shrinking",
    "ram_swap_overview",
    "swap",
    "caches",
    "active_and_inactive_memory",
    "active_and_inactive_memory_anon",
    "ram_used",
    "commit_charge",
    "filesystem_writeback",
    "memory_committing",
    "memory_that_cannot_be_swapped_out",
    "huge_pages",
    "huge_pages_2",
    "vmalloc_address_space_1",
    "vmalloc_address_space_2",
    "heap_and_non_heap_memory",
    "heap_memory_usage",
    "non-heap_memory_usage",
    "private_and_shared_memory",
    "harddrive_health_statistic",
    "mem_perm_used",
    "datafile_sizes",
    "files_notification_spool",
    "used_space",
    "io_flow",
    "varnish_backend_connections",
    "varnish_cache",
    "varnish_clients",
    "varnish_esi_errors_and_warnings",
    "varnish_fetch",
    "varnish_objects",
    "varnish_worker",
]
