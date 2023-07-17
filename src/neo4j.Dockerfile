# Use the official Neo4j image as the base image
FROM neo4j:5.9.0-enterprise

# Set the neo4j password
ENV NEO4J_AUTH=neo4j/neo4jpass

# Copy the local config file to the appropriate directory in the container
COPY ./neo4j.conf /var/lib/neo4j/conf

# # Set environment variables for APOC configuration
# ENV NEO4J_dbms_security_procedures_unrestricted=apoc.*
# ENV NEO4J_apoc_import_file_enabled=true
# ENV NEO4J_apoc_export_file_enabled=true
# ENV NEO4J_apoc_import_file_use__neo4j__config=true
# ENV NEO4J_apoc_export_file_use__neo4j__config=true
# ENV server.config.strict_validation.enabled=false

# # Download the APOC plugin
ARG APOC_VERSION=5.9.0
RUN wget "https://github.com/neo4j/apoc/releases/download/${APOC_VERSION}/apoc-${APOC_VERSION}-core.jar" -O "/var/lib/neo4j/plugins/apoc-${APOC_VERSION}-core.jar"