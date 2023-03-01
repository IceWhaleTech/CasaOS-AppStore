#!/bin/bash

set -e 

BUILD_PATH=$(dirname "${BASH_SOURCE[0]}")/../../..
readonly BUILD_PATH

DEFAULT_APPSTORE_PATH="${BUILD_PATH}/sysroot/var/lib/casaos/appstore/default"

mv -f "${DEFAULT_APPSTORE_PATH}" "${DEFAULT_APPSTORE_PATH}.old"
mv -f "${DEFAULT_APPSTORE_PATH}.new" "${DEFAULT_APPSTORE_PATH}" || {
    rm -f "${DEFAULT_APPSTORE_PATH}"
    mv -f "${DEFAULT_APPSTORE_PATH}.old" "${DEFAULT_APPSTORE_PATH}"
    rm -rf "${DEFAULT_APPSTORE_PATH}.new"
    exit 1
}
rm -rf "${DEFAULT_APPSTORE_PATH}.old"
