#!/usr/bin/python
# -*- coding: utf-8 -*-


def get_sandbox_msg(api, context):
    def sandbox_msg(msg):
        api.WriteMessageToReservationOutput(context.reservation.reservation_id, msg)
    return sandbox_msg
