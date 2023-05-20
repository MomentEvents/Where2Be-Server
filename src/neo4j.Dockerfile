# Use the official Neo4j image as the base image
FROM neo4j:4.4-enterprise

# Set environment variables for APOC configuration
ENV NEO4J_dbms_security_procedures_unrestricted=apoc.*
ENV NEO4J_apoc_import_file_enabled=true
ENV NEO4J_apoc_export_file_enabled=true
ENV NEO4J_apoc_import_file_use__neo4j__config=true
ENV NEO4J_apoc_export_file_use__neo4j__config=true

# Download the APOC plugin
ARG APOC_VERSION=4.4.0.0
RUN wget "https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/${APOC_VERSION}/apoc-${APOC_VERSION}-all.jar" -O "/var/lib/neo4j/plugins/apoc-${APOC_VERSION}-all.jar"